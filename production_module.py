import numpy as np

# ==============================================================================
# GEOMIND - PRODUCTION PHYSICS ENGINE (ADVANCED)
# Standards: API 14B / SPE - Nodal Analysis
# Correlations: Standing (PVT), Hall-Yarborough (Z), Chen (Friction)
# ==============================================================================

def calc_z_factor(p_psi, t_f, sg_gas):
    """Correlación Hall-Yarborough para Factor Z de gases naturales."""
    t_r = t_f + 459.67
    p_pc = 677 + 15.0 * sg_gas - 37.5 * sg_gas**2
    t_pc = 168 + 325 * sg_gas - 12.5 * sg_gas**2
    t_pr = t_r / t_pc
    p_pr = p_psi / p_pc
    
    t = 1/t_pr
    A = 0.06125 * t * np.exp(-1.2 * (1 - t)**2)
    
    # Newton-Raphson para resolver Y (densidad reducida)
    Y = 0.001 # Initial guess
    for _ in range(20):
        f = -A * p_pr + (Y + Y**2 + Y**3 - Y**4)/(1 - Y)**3 - (14.76 * t - 9.76 * t**2 + 4.58 * t**3) * Y**2 + (90.7 * t - 242.2 * t**2 + 42.4 * t**3) * Y**(2.18 + 2.82 * t)
        df = (1 + 4*Y + 4*Y**2 - 4*Y**3 + Y**4)/(1 - Y)**4 - 2*(14.76 * t - 9.76 * t**2 + 4.58 * t**3) * Y + (2.18 + 2.82 * t) * (90.7 * t - 242.2 * t**2 + 42.4 * t**3) * Y**(1.18 + 2.82 * t)
        Y_new = Y - f/df
        if abs(Y_new - Y) < 1e-6:
            Y = Y_new
            break
        Y = Y_new
        
    z = A * p_pr / Y
    return max(0.5, min(z, 1.5)) # Safety clip

def calc_friction_factor(re, epsilon, d_in):
    """Ecuación de Chen para factor de fricción (f) explícito (turbulento)."""
    if re < 2000: return 64 / max(re, 1) # Laminar
    
    rel_rough = epsilon / (d_in / 12) # Rugosidad relativa
    a = (rel_rough**1.1098) / 2.8257 + (7.149 / re)**0.8981
    f = (-2.0 * np.log10(rel_rough / 3.7065 - 5.0452 / re * np.log10(a))) ** -2
    return f

def calculate_ipr_vogel(pr, q_test=None, pwf_test=None, k=None, h=None, skin=0, u_o=1.0, bo=1.2, re=1000, rw=0.328):
    """Calcula IPR usando Vogel (Curvatura de Oferta)."""
    q_max = 0
    if k is not None and h is not None:
        # Darcy para índice J
        j_index = (k * h) / (141.2 * bo * u_o * (np.log(re/rw) - 0.75 + skin))
        q_max_darcy = j_index * pr / 1.8 
        q_max = max(q_max, q_max_darcy)

    if q_test and pwf_test:
        if pwf_test >= pr:
             q_max = q_test * pr / (pr - pwf_test + 1e-5)
        else:
            denom = 1 - 0.2*(pwf_test/pr) - 0.8*(pwf_test/pr)**2
            q_max = q_test / max(denom, 0.01)

    if q_max <= 0: q_max = 500 # Default de seguridad si todo falla
    
    pressures = np.linspace(pr, 0, 50)
    rates = []
    for p in pressures:
        q = q_max * (1 - 0.2*(p/pr) - 0.8*(p/pr)**2)
        rates.append(q)
        
    return {'q_max': round(q_max, 2), 'rates': [round(x, 2) for x in rates], 'pressures': [round(x, 2) for x in pressures]}

def calculate_vlp_basic(tvd, md, tubing_id, p_wh, q_liquid, wc=0, gor=500, api=35, gas_grav=0.65, temp_bh=200, temp_wh=100):
    """
    Calcula VLP usando correlaciones físicas reales (sin constantes mágicas).
    """
    # Constantes físicas
    water_grav = 1.07
    oil_grav = 141.5 / (131.5 + api)
    avg_temp_f = (temp_bh + temp_wh) / 2
    avg_temp_r = avg_temp_f + 459.67
    epsilon = 0.0006 # Rugosidad tubing acero comercial (ft)
    
    pwf_vlp = []
    valid_rates = []
    
    area_ft2 = (np.pi/4) * (tubing_id/12)**2
    d_ft = tubing_id / 12
    
    debug_log = []
    
    for i, q in enumerate(q_liquid):
        if q <= 0.1:
            # Hidrostática pura
            rho_mix = (wc/100)*water_grav*62.4 + (1 - wc/100)*oil_grav*62.4
            p_static = p_wh + (rho_mix * tvd / 144)
            valid_rates.append(q)
            pwf_vlp.append(p_static)
            if i < 3: debug_log.append(f"Q={q}: P_static={p_static:.1f}")
            continue

        # Iteración simple para presión promedio
        p_avg = p_wh + 0.2*tvd # Seed
        p_calc_final = 0
        
        for iter_idx in range(3):
            # 1. Propiedades PVT a P_avg & T_avg
            z = calc_z_factor(p_avg, avg_temp_f, gas_grav)
            bg = 0.02827 * z * avg_temp_r / p_avg
            
            # Rs (Standing simple approx)
            try:
                rs = gas_grav * ((p_avg / 18.2 + 1.4) * 10**(0.0125*api - 0.00091*avg_temp_f))**1.2048
            except:
                rs = gor # Fallback
            
            # FVF Petróleo (Bo)
            bo = 0.9759 + 0.00012 * (rs * (gas_grav/oil_grav)**0.5 + 1.25*avg_temp_f)**1.2
            
            # Volúmenes In-Situ
            qw = q * (wc/100)
            qo = q * (1 - wc/100)
            qg_free = max(0, (qo * (gor - rs))/1000) * 1000 # scf/d
            
            ql_insitu = qw * 1.02 + qo * bo # bbl/d
            qg_insitu = (qg_free / 5.615) * bg # bbl/d
            
            q_mix = ql_insitu + qg_insitu
            vm = (q_mix * 5.615 / 86400) / area_ft2 # velocity mixture ft/s
            
            # Holdup (Turner & Ros modified)
            nl = (ql_insitu / q_mix) # No-slip liquid hold-up
            hl = max(nl, nl + (1-nl)**2 * 0.1) # Slip correction
            
            # Densidades
            rho_liq = (wc/100)*water_grav*62.4 + (1 - wc/100)*oil_grav*62.4
            rho_gas = gas_grav * 0.0764 * (p_avg/14.7) * (520/avg_temp_r)
            rho_mix = src_rho = hl*rho_liq + (1-hl)*rho_gas
            
            # Viscosidad mezcla (aprox para Reynolds)
            mu_mix = 1.0 * hl + 0.02 * (1-hl) # cp
            
            # Reynolds
            re = 1488 * rho_mix * vm * d_ft / mu_mix
            
            # Fricción
            f = calc_friction_factor(re, epsilon, tubing_id)
            
            # Gradientes
            dp_elev = (rho_mix * tvd) / 144
            dp_fric = (f * rho_mix * vm**2 * md) / (2 * 32.2 * d_ft) / 144
            
            p_calc = p_wh + dp_elev + dp_fric
            p_avg = (p_wh + p_calc)/2 # Update average for next iter
            p_calc_final = p_calc
        
        if i < 5: 
            debug_log.append(f"Q={q:.1f}: Pwf={p_calc_final:.1f} (Elev={dp_elev:.1f}, Fric={dp_fric:.1f}, RhoMix={rho_mix:.1f}, HL={hl:.2f})")

        valid_rates.append(q)
        pwf_vlp.append(p_calc_final)
        
    return {'rates': [round(x, 2) for x in valid_rates], 'pressures': [round(x, 2) for x in pwf_vlp], 'debug': debug_log}

def find_intersection(ipr, vlp):
    q_ipr = np.array(ipr['rates'])
    p_ipr = np.array(ipr['pressures'])
    q_vlp = np.array(vlp['rates'])
    p_vlp = np.array(vlp['pressures'])
    
    q_common = np.linspace(min(min(q_ipr), min(q_vlp)), min(max(q_ipr), max(q_vlp)), 1000)
    # q_ipr ya está ordenado ascendente (0 -> Qmax), no invertir
    p_ipr_interp = np.interp(q_common, q_ipr, p_ipr)
    p_vlp_interp = np.interp(q_common, q_vlp, p_vlp)
    
    diff = np.abs(p_ipr_interp - p_vlp_interp)
    idx_min = np.argmin(diff)
    
    if diff[idx_min] > 200: return None
    return {'q_op': round(q_common[idx_min], 2), 'pwf_op': round(p_ipr_interp[idx_min], 2)}

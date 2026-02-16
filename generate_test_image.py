
import numpy as np
import matplotlib.pyplot as plt

def generate_synthetic_seismic(filename="test_seismic.png"):
    # Parámetros
    nx, nt = 400, 600
    data = np.zeros((nt, nx))
    
    # Generar reflectores horizontales con ruido
    t = np.arange(nt)
    for i in range(10, nt, 40):
        wavelet = np.exp(-(t-i)**2 / 100) * np.sin(0.2 * t)
        for x in range(nx):
            # Simular una FALLA NORMAL en x=200
            offset = 30 if x > 200 else 0
            if i + offset < nt:
                data[i + offset, x] = wavelet[i]
    
    # Añadir un poco de "ruido estratigráfico"
    data += np.random.normal(0, 0.05, data.shape)
    
    # Graficar y guardar
    plt.figure(figsize=(10, 6))
    plt.imshow(data, cmap='gray', aspect='auto')
    plt.title("Synthetic Seismic Section - Challenge: Find the Fault at X=200")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Imagen de prueba generada: {filename}")

if __name__ == "__main__":
    generate_synthetic_seismic()

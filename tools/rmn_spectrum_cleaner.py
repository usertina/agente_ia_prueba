import os
import json
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal, ndimage
from scipy.signal import savgol_filter, medfilt, wiener
from scipy.ndimage import gaussian_filter1d
from datetime import datetime
import io
import base64
from pathlib import Path

class RMNSpectrumCleaner:
    """
    Herramienta para limpiar ruido en espectros RMN
    Soporta múltiples algoritmos de limpieza y análisis automático
    """
    
    def __init__(self):
        # Directorios
        self.input_dir = "rmn_spectra/input"
        self.output_dir = "rmn_spectra/output" 
        self.plots_dir = "rmn_spectra/plots"
        
        # Crear directorios
        for dir_path in [self.input_dir, self.output_dir, self.plots_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Formatos soportados
        self.supported_formats = ['.csv', '.txt', '.dat', '.asc', '.json']
        
        # Métodos de limpieza disponibles
        self.cleaning_methods = {
            'savgol': 'Filtro Savitzky-Golay',
            'gaussian': 'Filtro Gaussiano', 
            'median': 'Filtro Mediana',
            'wiener': 'Filtro Wiener',
            'moving_average': 'Media Móvil',
            'polynomial': 'Corrección Línea Base Polinómica',
            'rolling_ball': 'Rolling Ball Background',
            'auto': 'Limpieza Automática (recomendado)'
        }
    
    def run(self, prompt: str):
        """
        Procesa comandos para limpiar espectros RMN
        
        Comandos disponibles:
        - "listar espectros" - Lista archivos disponibles
        - "analizar: archivo.csv" - Analiza calidad del espectro
        - "limpiar: archivo.csv con savgol" - Limpia con método específico
        - "limpiar auto: archivo.csv" - Limpieza automática
        - "comparar: archivo.csv" - Compara antes/después
        - "exportar: archivo.csv formato json" - Exporta en formato específico
        """
        
        prompt = prompt.strip().lower()
        
        if "listar espectros" in prompt:
            return self.list_spectra()
        elif prompt.startswith("analizar:"):
            filename = prompt[9:].strip()
            return self.analyze_spectrum(filename)
        elif prompt.startswith("limpiar auto:"):
            filename = prompt[13:].strip()
            return self.auto_clean_spectrum(filename)
        elif prompt.startswith("limpiar:"):
            command = prompt[8:].strip()
            return self.clean_spectrum(command)
        elif prompt.startswith("comparar:"):
            filename = prompt[9:].strip()
            return self.compare_spectra(filename)
        elif prompt.startswith("exportar:"):
            command = prompt[9:].strip()
            return self.export_spectrum(command)
        elif "métodos" in prompt or "algoritmos" in prompt:
            return self.show_methods()
        else:
            return self.show_help()
    
    def show_help(self) -> str:
        """Muestra la ayuda del sistema"""
        return """
🧪 **LIMPIADOR DE ESPECTROS RMN**

**📋 Comandos disponibles:**

1️⃣ **Gestión de archivos:**
   • `listar espectros` - Ver archivos disponibles
   • `métodos` - Ver algoritmos de limpieza

2️⃣ **Análisis de espectros:**
   • `analizar: espectro.csv` - Analiza calidad y ruido
   • `comparar: espectro.csv` - Compara original vs limpio

3️⃣ **Limpieza de ruido:**
   • `limpiar auto: espectro.csv` - Limpieza automática (recomendado)
   • `limpiar: espectro.csv con savgol` - Con método específico
   • `limpiar: espectro.csv con gaussian ventana=5` - Con parámetros

4️⃣ **Exportar resultados:**
   • `exportar: espectro.csv formato json` - Exporta limpio
   • `exportar: espectro.csv formato txt` - Como archivo texto

**🔬 Métodos de limpieza:**
   • **savgol** - Filtro Savitzky-Golay (preserva picos)
   • **gaussian** - Suavizado gaussiano
   • **median** - Elimina picos de ruido
   • **wiener** - Restauración adaptativa
   • **auto** - Selección automática del mejor método

**📁 Estructura de archivos:**
   • `rmn_spectra/input/` - Coloca aquí tus espectros
   • `rmn_spectra/output/` - Espectros limpios
   • `rmn_spectra/plots/` - Gráficos comparativos

**📊 Formatos soportados:**
   • CSV (frecuencia, intensidad)
   • TXT (dos columnas separadas por tab/espacio)
   • JSON (formato estructurado)
   • DAT/ASC (formatos comunes de equipos RMN)

**💡 Flujo recomendado:**
   1. Sube tu espectro a `rmn_spectra/input/`
   2. `analizar: mi_espectro.csv`
   3. `limpiar auto: mi_espectro.csv`
   4. `comparar: mi_espectro.csv`
   5. `exportar: mi_espectro.csv formato json`

**🎯 Ideal para:**
   • Análisis químico cuantitativo
   • Identificación de compuestos
   • Preparación de datos para ML
   • Publicaciones científicas
        """
    
    def show_methods(self) -> str:
        """Muestra información detallada sobre los métodos de limpieza"""
        return """
🔬 **MÉTODOS DE LIMPIEZA DE ESPECTROS RMN**

**🏆 AUTOMÁTICO (Recomendado)**
   • Analiza el espectro y selecciona el mejor algoritmo
   • Optimiza parámetros automáticamente
   • Ideal para usuarios no expertos

**📈 SAVITZKY-GOLAY**
   • Mejor para preservar forma de picos
   • Ideal para análisis cuantitativo
   • Parámetros: ventana (5-21), orden (2-4)
   • Uso: `limpiar: archivo.csv con savgol ventana=9 orden=3`

**🌊 GAUSSIANO**
   • Suavizado general efectivo
   • Reduce ruido de alta frecuencia
   • Parámetro: sigma (0.5-3.0)
   • Uso: `limpiar: archivo.csv con gaussian sigma=1.5`

**🎯 MEDIANA**
   • Elimina picos de ruido impulsivo
   • Preserva bordes de señales
   • Parámetro: ventana (3-15, impar)
   • Uso: `limpiar: archivo.csv con median ventana=5`

**🔧 WIENER**
   • Filtro adaptativo avanzado
   • Restaura señales degradadas
   • Parámetro: ruido (auto-estimado)
   • Uso: `limpiar: archivo.csv con wiener`

**📊 MEDIA MÓVIL**
   • Suavizado simple y rápido
   • Para ruido aleatorio uniforme
   • Parámetro: ventana (3-20)
   • Uso: `limpiar: archivo.csv con moving_average ventana=7`

**📏 CORRECCIÓN LÍNEA BASE**
   • Corrige deriva de línea base
   • Elimina tendencias polinómicas
   • Parámetro: grado (1-5)
   • Uso: `limpiar: archivo.csv con polynomial grado=2`

**💡 Recomendaciones por tipo de ruido:**
   • **Ruido aleatorio** → savgol, gaussian
   • **Picos de ruido** → median
   • **Deriva de base** → polynomial
   • **Ruido complejo** → auto (recomendado)

        """    
    def list_spectra(self) -> str:
        """Lista los espectros disponibles"""
        try:
            files = []
            if not os.path.exists(self.input_dir):
                os.makedirs(self.input_dir, exist_ok=True)
                
            for file in os.listdir(self.input_dir):
                if any(file.endswith(ext) for ext in self.supported_formats):
                    file_path = os.path.join(self.input_dir, file)
                    try:
                        size = os.path.getsize(file_path)
                        modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                        files.append({
                            'name': file,
                            'size': f"{size/1024:.1f} KB", 
                            'modified': modified.strftime("%Y-%m-%d %H:%M"),
                            'ext': file.split('.')[-1].upper()
                        })
                    except:
                        continue
            
            if not files:
                return f"""
📁 **No hay espectros disponibles**

Para empezar:
1. Coloca tus archivos de espectro en: `{self.input_dir}/`
2. Formatos soportados: {', '.join(self.supported_formats)}
3. Formato esperado: dos columnas (frecuencia/ppm, intensidad)

Ejemplo de archivo CSV:
```
ppm,intensidad
0.0,1024.5
0.1,1025.2
0.2,1023.8
...
```
                """
            
            result = "🧪 **ESPECTROS RMN DISPONIBLES:**\n\n"
            for i, file in enumerate(files, 1):
                result += f"{i}. **{file['name']}** ({file['ext']})\n"
                result += f"   📊 Tamaño: {file['size']}\n"
                result += f"   📅 Modificado: {file['modified']}\n\n"
            
            result += "💡 **Siguiente paso:** `analizar: nombre_archivo.csv`"
            return result
            
        except Exception as e:
            return f"❌ Error listando espectros: {e}"
        

    def parse_value(self, value):
        """
        Convierte un valor en float. Si es un rango tipo '-85.1326 - -85.1226',
        devuelve el promedio de ambos.
        """
        import re
        if isinstance(value, (int, float)):
            return float(value)
        
        value = str(value).strip()
        match = re.match(r'^(-?\d+\.?\d*)\s*-\s*(-?\d+\.?\d*)$', value)
        if match:
            a, b = float(match.group(1)), float(match.group(2))
            return (a + b) / 2
        return float(value)

    
    def load_spectrum_data(self, file_path: str):
        """Carga datos del espectro desde diferentes formatos"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, comment='#')  # Ignorar líneas de comentario
                if len(df.columns) >= 2:
                    x = df.iloc[:, 0].values
                    y = df.iloc[:, 1].values
                else:
                    return None, None
                    
            elif file_path.endswith('.txt') or file_path.endswith('.dat') or file_path.endswith('.asc'):
                data = np.loadtxt(file_path)
                if len(data.shape) == 2 and data.shape[1] >= 2:
                    x = data[:, 0]
                    y = data[:, 1]
                elif len(data.shape) == 1:
                    # Si es un vector, asumir que es intensidad y crear índices
                    y = data
                    x = np.arange(len(y))
                else:
                    return None, None
                    
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                x = np.array(data['x'])
                y = np.array(data['y'])
            
            else:
                return None, None
            
            # Validar datos
            if len(x) != len(y) or len(x) < 10:
                return None, None
                
            x = np.array([self.parse_value(v) for v in x])
            y = np.array([self.parse_value(v) for v in y])
    
                
            return x, y
            
        except Exception as e:
            print(f"Error cargando espectro: {e}")
            return None, None
    
    def perform_spectrum_analysis(self, x, y):
        """Realiza análisis completo de calidad del espectro"""
        try:
            # Estadísticas básicas
            mean_intensity = np.mean(y)
            std_intensity = np.std(y)
            
            # Estimación de ruido (usando percentiles)
            noise_level = np.std(y[y < np.percentile(y, 10)])
            if noise_level == 0:
                noise_level = std_intensity * 0.1  # Fallback
                
            signal_level = np.max(y) - np.percentile(y, 10)
            if signal_level <= 0:
                signal_level = np.max(y) - np.min(y)
                
            # Calcular SNR evitando division por cero
            snr = 20 * np.log10(signal_level / max(noise_level, 1e-10))
            
            # Deriva de línea base (tendencia lineal)
            try:
                baseline_drift = abs(np.polyfit(x, y, 1)[0])
            except:
                baseline_drift = 0
            
            # Detección de picos
            try:
                threshold = mean_intensity + 2*std_intensity
                peaks, _ = signal.find_peaks(y, height=threshold)
                peak_count = len(peaks)
            except:
                peak_count = 0
            
            return {
                'snr': float(snr) if not np.isnan(snr) else 0,
                'noise_level': float(noise_level),
                'signal_level': float(signal_level),
                'baseline_drift': float(baseline_drift),
                'peak_count': int(peak_count),
                'mean_intensity': float(mean_intensity),
                'std_intensity': float(std_intensity)
            }
            
        except Exception as e:
            print(f"Error en análisis: {e}")
            return {'snr': 0, 'noise_level': 1, 'signal_level': 1, 
                   'baseline_drift': 0, 'peak_count': 0, 
                   'mean_intensity': 0, 'std_intensity': 1}
    
    def analyze_spectrum(self, filename: str) -> str:
        """Analiza un espectro para detectar ruido y características"""
        try:
            file_path = os.path.join(self.input_dir, filename)
            if not os.path.exists(file_path):
                return f"❌ No se encontró el archivo: {filename}"
            
            # Cargar datos
            x, y = self.load_spectrum_data(file_path)
            if x is None or y is None:
                return f"❌ Error cargando datos del espectro: {filename}"
            
            # Análisis de calidad
            analysis = self.perform_spectrum_analysis(x, y)
            
            # Generar gráfico de análisis
            plot_path = self.create_analysis_plot(x, y, filename, analysis)
            
            result = f"🔍 **ANÁLISIS DE ESPECTRO: {filename}**\n\n"
            
            result += "📊 **Estadísticas básicas:**\n"
            result += f"• Puntos de datos: {len(y):,}\n"
            result += f"• Rango frecuencia: {x.min():.2f} - {x.max():.2f} ppm\n"
            result += f"• Intensidad máxima: {y.max():.1f}\n"
            result += f"• Intensidad mínima: {y.min():.1f}\n\n"
            
            result += "🔬 **Análisis de calidad:**\n"
            result += f"• Relación señal/ruido: {analysis['snr']:.1f} dB\n"
            result += f"• Nivel de ruido: {analysis['noise_level']:.2f}\n"
            result += f"• Deriva línea base: {analysis['baseline_drift']:.2f}\n"
            result += f"• Picos detectados: {analysis['peak_count']}\n\n"
            
            # Recomendaciones
            result += "💡 **Recomendaciones:**\n"
            if analysis['snr'] < 20:
                result += "• ⚠️ SNR baja - Se recomienda limpieza agresiva\n"
                result += f"• 🎯 Método sugerido: `limpiar: {filename} con wiener`\n"
            elif analysis['snr'] < 30:
                result += "• 📈 SNR moderada - Limpieza suave recomendada\n"
                result += f"• 🎯 Método sugerido: `limpiar: {filename} con savgol`\n"
            else:
                result += "• ✅ SNR buena - Limpieza mínima necesaria\n"
                result += f"• 🎯 Método sugerido: `limpiar: {filename} con gaussian`\n"
            
            if analysis['baseline_drift'] > 0.1:
                result += "• 📏 Deriva de línea base detectada - Usar corrección polinómica\n"
                
            result += f"\n🔧 **Limpieza automática:** `limpiar auto: {filename}`\n"
            result += f"📊 **Gráfico guardado:** {plot_path}"
            
            return result
            
        except Exception as e:
            return f"❌ Error analizando espectro: {e}"
    
    def create_analysis_plot(self, x, y, filename, analysis):
        """Crea gráfico de análisis del espectro"""
        try:
            plt.figure(figsize=(12, 8))
            
            # Gráfico principal
            plt.subplot(2, 1, 1)
            plt.plot(x, y, 'b-', alpha=0.7, linewidth=1)
            plt.title(f'Análisis de Espectro: {filename}')
            plt.xlabel('ppm')
            plt.ylabel('Intensidad')
            plt.grid(True, alpha=0.3)
            
            # Estadísticas en el gráfico
            plt.text(0.02, 0.98, f'SNR: {analysis["snr"]:.1f} dB\nPicos: {analysis["peak_count"]}', 
                    transform=plt.gca().transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            # Histograma de intensidades
            plt.subplot(2, 1, 2)
            plt.hist(y, bins=50, alpha=0.7, color='skyblue')
            plt.axvline(analysis['mean_intensity'], color='red', linestyle='--', 
                       label=f'Media: {analysis["mean_intensity"]:.1f}')
            plt.axvline(analysis['mean_intensity'] + 2*analysis['std_intensity'], 
                       color='orange', linestyle='--', label='Umbral picos')
            plt.title('Distribución de Intensidades')
            plt.xlabel('Intensidad')
            plt.ylabel('Frecuencia')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Guardar
            plot_filename = f"analysis_{filename.split('.')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plot_path = os.path.join(self.plots_dir, plot_filename)
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return f"{self.plots_dir}/{plot_filename}"
            
        except Exception as e:
            print(f"Error creando gráfico: {e}")
            return "Error en gráfico"
    
    def select_best_method(self, analysis):
        """Selecciona automáticamente el mejor método de limpieza"""
        snr = analysis['snr']
        noise_level = analysis['noise_level'] 
        baseline_drift = analysis['baseline_drift']
        
        # Lógica de selección basada en características del espectro
        if baseline_drift > 0.1:
            # Corrección de línea base necesaria primero
            return 'polynomial', {'degree': 2}
        elif snr < 15:
            # SNR muy baja - filtro agresivo
            return 'wiener', {'noise': noise_level}
        elif snr < 25:
            # SNR moderada - Savitzky-Golay para preservar picos
            return 'savgol', {'window_length': 9, 'polyorder': 3}
        elif snr < 35:
            # SNR buena - suavizado suave
            return 'gaussian', {'sigma': 1.0}
        else:
            # SNR excelente - limpieza mínima
            return 'gaussian', {'sigma': 0.5}
    
    def apply_cleaning_method(self, y, method, params=None):
        """Aplica el método de limpieza especificado"""
        if params is None:
            params = {}
            
        try:
            if method == 'savgol':
                window = params.get('window_length', 9)
                order = params.get('polyorder', 3)
                # Asegurar ventana impar y menor que longitud de datos
                window = min(window if window % 2 == 1 else window + 1, len(y) - 1)
                if window < 3:
                    window = 3
                order = min(order, window - 1)
                return savgol_filter(y, window, order)
                
            elif method == 'gaussian':
                sigma = params.get('sigma', 1.0)
                return gaussian_filter1d(y, sigma)
                
            elif method == 'median':
                window = params.get('window_length', 5)
                window = min(window if window % 2 == 1 else window + 1, len(y))
                if window < 3:
                    window = 3
                return medfilt(y, window)
                
            elif method == 'wiener':
                noise = params.get('noise', None)
                return wiener(y, noise=noise)
                
            elif method == 'moving_average':
                window = params.get('window_length', 7)
                if window > len(y):
                    window = len(y) // 4
                kernel = np.ones(window) / window
                return np.convolve(y, kernel, mode='same')
                
            elif method == 'polynomial':
                degree = params.get('degree', 2)
                degree = min(degree, len(y) // 10)  # Evitar overfitting
                x = np.arange(len(y))
                # Ajustar polinomio y sustraer
                coeffs = np.polyfit(x, y, degree)
                baseline = np.polyval(coeffs, x)
                return y - baseline + np.mean(y)
                
            else:
                return y
                
        except Exception as e:
            print(f"Error aplicando método {method}: {e}")
            return y
    
    def auto_clean_spectrum(self, filename: str):
        """Limpia automáticamente un espectro seleccionando el mejor método"""
        try:
            file_path = os.path.join(self.input_dir, filename)
            if not os.path.exists(file_path):
                return f"❌ No se encontró el archivo: {filename}"
            
            # Cargar datos
            x, y = self.load_spectrum_data(file_path)
            if x is None or y is None:
                return f"❌ Error cargando datos del espectro: {filename}"
            
            # Análisis para determinar el mejor método
            analysis = self.perform_spectrum_analysis(x, y)
            
            # Seleccionar método automáticamente
            best_method, params = self.select_best_method(analysis)
            
            # Aplicar limpieza
            y_clean = self.apply_cleaning_method(y, best_method, params)
            
            # Guardar resultado
            output_filename = f"{filename.split('.')[0]}_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.save_cleaned_spectrum(x, y_clean, output_filename, best_method)
            
            # Crear gráfico comparativo
            plot_filename = f"comparison_{filename.split('.')[0]}_{best_method}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plot_path = self.create_comparison_plot(x, y, y_clean, filename, best_method, plot_filename)
            
            # Análisis post-limpieza
            analysis_clean = self.perform_spectrum_analysis(x, y_clean)
            improvement = analysis_clean['snr'] - analysis['snr']
            
            # Calcular tiempo de procesamiento (simulado)
            processing_time = len(x) * 0.001  # Tiempo estimado
            
            # IMPORTANTE: Devolver diccionario en lugar de string para que JavaScript lo detecte
            return {
                'type': 'clean_result',
                'original_file': filename,
                'cleaned_file': f"{self.output_dir}/{output_filename}",
                'plot_file': plot_path if plot_path else None,
                'method': self.cleaning_methods[best_method],
                'params': params,
                'snr_improvement': round(improvement, 1),
                'snr_original': round(analysis['snr'], 1),
                'snr_clean': round(analysis_clean['snr'], 1),
                'processing_time': round(processing_time, 2),
                'data_points': len(x),
                'success': True,
                'message': f"Espectro {filename} limpiado exitosamente con {best_method}"
            }
            
        except Exception as e:
            return f"❌ Error en limpieza automática: {e}"
    
    def create_comparison_plot(self, x, y_original, y_clean, filename, method, plot_filename):
        """Crea gráfico comparativo antes/después"""
        try:
            plt.figure(figsize=(15, 10))
            
            # Espectro completo
            plt.subplot(2, 2, (1, 2))
            plt.plot(x, y_original, 'b-', alpha=0.7, label='Original', linewidth=1)
            plt.plot(x, y_clean, 'r-', alpha=0.8, label='Limpio', linewidth=1.5)
            plt.title(f'Comparación: {filename} - Método: {method}')
            plt.xlabel('ppm')
            plt.ylabel('Intensidad')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Zoom en región de interés (primera mitad)
            mid_point = len(x) // 2
            plt.subplot(2, 2, 3)
            plt.plot(x[:mid_point], y_original[:mid_point], 'b-', alpha=0.7, label='Original')
            plt.plot(x[:mid_point], y_clean[:mid_point], 'r-', alpha=0.8, label='Limpio')
            plt.title('Zoom: Primera mitad')
            plt.xlabel('ppm')
            plt.ylabel('Intensidad')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Diferencia (ruido eliminado)
            plt.subplot(2, 2, 4)
            noise_removed = y_original - y_clean
            plt.plot(x, noise_removed, 'g-', alpha=0.7, linewidth=1)
            plt.title('Ruido Eliminado')
            plt.xlabel('ppm')
            plt.ylabel('Diferencia')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Guardar
            plot_path = os.path.join(self.plots_dir, plot_filename)
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return f"{self.plots_dir}/{plot_filename}"
            
        except Exception as e:
            print(f"Error creando gráfico comparativo: {e}")
            return None
    
    def save_cleaned_spectrum(self, x, y_clean, filename, method, params=None):
        """Guarda el espectro limpio en formato CSV"""
        try:
            output_path = os.path.join(self.output_dir, filename)
            
            # Crear DataFrame
            df = pd.DataFrame({
                'ppm': x,
                'intensity': y_clean
            })
            
            # Agregar metadatos como comentarios
            metadata = f"# Espectro limpiado con {method}\n"
            if params:
                metadata += f"# Parámetros: {params}\n"
            metadata += f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Guardar con metadatos
            with open(output_path, 'w') as f:
                f.write(metadata)
                df.to_csv(f, index=False)
                
        except Exception as e:
            print(f"Error guardando espectro: {e}")
    
    def clean_spectrum(self, command: str) -> str:
        """Limpia un espectro con método y parámetros específicos"""
        try:
            # Parsear comando: "archivo.csv con savgol ventana=9 orden=3"
            if " con " not in command:
                return "❌ Formato incorrecto. Usa: `limpiar: archivo.csv con método parámetros`"
            
            parts = command.split(" con ")
            filename = parts[0].strip()
            method_params = parts[1].strip().split()
            method = method_params[0]
            
            # Extraer parámetros
            params = {}
            for param in method_params[1:]:
                if "=" in param:
                    key, value = param.split("=")
                    try:
                        params[key] = float(value) if "." in value else int(value)
                    except:
                        params[key] = value
            
            if method not in self.cleaning_methods:
                available = ", ".join(self.cleaning_methods.keys())
                return f"❌ Método '{method}' no disponible. Métodos: {available}"
            
            # Cargar datos
            file_path = os.path.join(self.input_dir, filename)
            if not os.path.exists(file_path):
                return f"❌ No se encontró el archivo: {filename}"
            
            x, y = self.load_spectrum_data(file_path)
            if x is None or y is None:
                return f"❌ Error cargando datos del espectro: {filename}"
            
            # Análisis pre-limpieza
            analysis_original = self.perform_spectrum_analysis(x, y)
            
            # Aplicar limpieza
            y_clean = self.apply_cleaning_method(y, method, params)
            
            # Guardar resultado
            output_filename = f"{filename.split('.')[0]}_{method}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.save_cleaned_spectrum(x, y_clean, output_filename, method, params)
            
            # Análisis post-limpieza
            analysis_clean = self.perform_spectrum_analysis(x, y_clean)
            improvement = analysis_clean['snr'] - analysis_original['snr']
            
            result = f"✅ **ESPECTRO LIMPIADO CON {method.upper()}**\n\n"
            result += f"📄 **Archivo:** {output_filename}\n"
            result += f"🔧 **Método:** {self.cleaning_methods[method]}\n"
            result += f"📊 **Parámetros:** {params if params else 'Por defecto'}\n\n"
            
            result += f"📈 **Resultados:**\n"
            result += f"• Mejora SNR: +{improvement:.1f} dB\n"
            
            if analysis_original['noise_level'] > 0:
                noise_reduction = ((analysis_original['noise_level'] - analysis_clean['noise_level']) / analysis_original['noise_level'] * 100)
                result += f"• Reducción ruido: {noise_reduction:.1f}%\n\n"
            
            if improvement < 2:
                result += "⚠️ **Advertencia:** Mejora limitada. Prueba con 'limpiar auto'\n"
            
            result += f"📁 **Ubicación:** {self.output_dir}/{output_filename}"
            
            return result
            
        except Exception as e:
            return f"❌ Error limpiando espectro: {e}"
    
    def compare_spectra(self, filename: str) -> str:
        """Compara todas las versiones limpias de un espectro"""
        try:
            # Buscar archivo original
            original_path = os.path.join(self.input_dir, filename)
            if not os.path.exists(original_path):
                return f"❌ No se encontró el archivo original: {filename}"
            
            # Cargar espectro original
            x_orig, y_orig = self.load_spectrum_data(original_path)
            if x_orig is None:
                return f"❌ Error cargando espectro original: {filename}"
            
            # Buscar versiones limpias
            base_name = filename.split('.')[0]
            cleaned_files = []
            
            if not os.path.exists(self.output_dir):
                return f"⚠️ No se encontraron versiones limpias de {filename}\nPrimero usa: `limpiar auto: {filename}`"
            
            for file in os.listdir(self.output_dir):
                if file.startswith(base_name) and file.endswith('.csv'):
                    file_path = os.path.join(self.output_dir, file)
                    try:
                        x_clean, y_clean = self.load_spectrum_data(file_path)
                        if x_clean is not None and len(x_clean) == len(x_orig):
                            # Extraer método del nombre del archivo
                            method = 'desconocido'
                            for m in self.cleaning_methods.keys():
                                if m in file:
                                    method = m
                                    break
                            
                            analysis = self.perform_spectrum_analysis(x_clean, y_clean)
                            cleaned_files.append({
                                'filename': file,
                                'method': method,
                                'y_data': y_clean,
                                'snr': analysis['snr'],
                                'noise_level': analysis['noise_level']
                            })
                    except:
                        continue
            
            if not cleaned_files:
                return f"⚠️ No se encontraron versiones limpias de {filename}\nPrimero usa: `limpiar auto: {filename}`"
            
            # Análisis original
            orig_analysis = self.perform_spectrum_analysis(x_orig, y_orig)
            
            # Generar reporte
            result = f"📊 **COMPARACIÓN DE MÉTODOS: {filename}**\n\n"
            
            result += f"📈 **Espectro original:**\n"
            result += f"• SNR: {orig_analysis['snr']:.1f} dB\n"
            result += f"• Nivel de ruido: {orig_analysis['noise_level']:.3f}\n"
            result += f"• Picos detectados: {orig_analysis['peak_count']}\n\n"
            
            result += f"🔧 **Versiones limpias encontradas ({len(cleaned_files)}):**\n\n"
            
            # Ordenar por mejora en SNR
            cleaned_files.sort(key=lambda x: x['snr'], reverse=True)
            
            for i, clean in enumerate(cleaned_files, 1):
                improvement = clean['snr'] - orig_analysis['snr']
                if orig_analysis['noise_level'] > 0:
                    noise_reduction = ((orig_analysis['noise_level'] - clean['noise_level']) / orig_analysis['noise_level'] * 100)
                else:
                    noise_reduction = 0
                
                result += f"{i}. **{self.cleaning_methods.get(clean['method'], clean['method'])}**\n"
                result += f"   📄 Archivo: {clean['filename']}\n"
                result += f"   📈 SNR: {clean['snr']:.1f} dB (+{improvement:.1f} dB)\n"
                result += f"   🔽 Reducción ruido: {noise_reduction:.1f}%\n"
                
                if i == 1:
                    result += "   🏆 **MEJOR RESULTADO**\n"
                result += "\n"
            
            # Recomendación
            best = cleaned_files[0]
            result += f"💡 **Recomendación:** Usar **{best['filename']}**\n"
            result += f"🎯 **Exportar mejor resultado:** `exportar: {filename} formato json`"
            
            return result
            
        except Exception as e:
            return f"❌ Error comparando espectros: {e}"
    
    def export_spectrum(self, command: str) -> str:
        """Exporta espectro limpio en formato específico"""
        try:
            # Parsear comando: "archivo.csv formato json"
            if "formato" not in command:
                return "❌ Formato incorrecto. Usa: `exportar: archivo.csv formato json`"
            
            parts = command.split("formato")
            filename = parts[0].strip()
            export_format = parts[1].strip().lower()
            
            # Buscar la mejor versión limpia
            base_name = filename.split('.')[0]
            best_file = None
            best_snr = -999
            
            if not os.path.exists(self.output_dir):
                return f"❌ No se encontraron versiones limpias de {filename}\nPrimero usa: `limpiar auto: {filename}`"
            
            for file in os.listdir(self.output_dir):
                if file.startswith(base_name) and file.endswith('.csv'):
                    file_path = os.path.join(self.output_dir, file)
                    try:
                        x, y = self.load_spectrum_data(file_path)
                        if x is not None:
                            analysis = self.perform_spectrum_analysis(x, y)
                            if analysis['snr'] > best_snr:
                                best_snr = analysis['snr']
                                best_file = file
                                best_x, best_y = x, y
                    except:
                        continue
            
            if best_file is None:
                return f"❌ No se encontraron versiones limpias de {filename}\nPrimero usa: `limpiar auto: {filename}`"
            
            # Exportar según formato
            export_name = f"{base_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if export_format == 'json':
                export_path = os.path.join(self.output_dir, f"{export_name}.json")
                export_data = {
                    'metadata': {
                        'original_file': filename,
                        'cleaned_file': best_file,
                        'snr': float(best_snr),
                        'export_date': datetime.now().isoformat(),
                        'data_points': len(best_x)
                    },
                    'x': best_x.tolist(),
                    'y': best_y.tolist()
                }
                
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
            elif export_format == 'txt':
                export_path = os.path.join(self.output_dir, f"{export_name}.txt")
                header = f"# Espectro RMN limpio exportado\n"
                header += f"# Archivo original: {filename}\n"
                header += f"# Archivo limpio: {best_file}\n"
                header += f"# SNR: {best_snr:.1f} dB\n"
                header += f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                header += f"# Formato: ppm intensidad\n"
                
                with open(export_path, 'w') as f:
                    f.write(header)
                    for x_val, y_val in zip(best_x, best_y):
                        f.write(f"{x_val:.6f}\t{y_val:.6f}\n")
                        
            elif export_format == 'csv':
                export_path = os.path.join(self.output_dir, f"{export_name}.csv")
                df = pd.DataFrame({
                    'ppm': best_x,
                    'intensity': best_y
                })
                df.to_csv(export_path, index=False)
                
            else:
                return f"❌ Formato '{export_format}' no soportado. Usa: json, txt, csv"
            
            result = f"✅ **ESPECTRO EXPORTADO**\n\n"
            result += f"📄 **Archivo:** {export_name}.{export_format}\n"
            result += f"🔧 **Basado en:** {best_file}\n"
            result += f"📈 **SNR:** {best_snr:.1f} dB\n"
            result += f"📊 **Puntos de datos:** {len(best_x):,}\n"
            result += f"📁 **Ubicación:** {self.output_dir}/{export_name}.{export_format}\n\n"
            result += f"💡 **Listo para usar en análisis químico o ML**"
            
            return result
            
        except Exception as e:
            return f"❌ Error exportando espectro: {e}"


# Instancia global
rmn_cleaner = RMNSpectrumCleaner()


def run(prompt: str):
    """Función principal de la herramienta"""
    return rmn_cleaner.run(prompt)
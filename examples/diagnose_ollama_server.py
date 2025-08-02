"""
Script de diagnóstico para servidor Ollama de UPV
Prueba diferentes configuraciones para encontrar la correcta
"""

import requests
import socket
from urllib.parse import urlparse
import ssl

def test_port_connectivity(host, port, timeout=5):
    """Prueba si un puerto está abierto y accesible"""
    try:
        sock = socket.create_connection((host, port), timeout)
        sock.close()
        return True
    except (socket.timeout, socket.error):
        return False

def test_https_connectivity(host, port=443, timeout=5):
    """Prueba conectividad HTTPS"""
    try:
        context = ssl.create_default_context()
        sock = socket.create_connection((host, port), timeout)
        ssock = context.wrap_socket(sock, server_hostname=host)
        ssock.close()
        return True
    except (socket.timeout, socket.error, ssl.SSLError):
        return False

def test_ollama_endpoint(base_url, endpoint="/api/tags", timeout=10):
    """Prueba un endpoint específico de Ollama"""
    try:
        url = f"{base_url.rstrip('/')}{endpoint}"
        print(f"🔍 Probando: {url}")
        
        response = requests.get(url, timeout=timeout)
        print(f"  ✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'models' in data:
                    print(f"  🎯 ¡ENDPOINT CORRECTO! Encontrados {len(data['models'])} modelos")
                    return True, data
                else:
                    print(f"  📄 Respuesta: {response.text[:200]}")
            except:
                print(f"  📄 Respuesta (no JSON): {response.text[:200]}")
        else:
            print(f"  ❌ Error HTTP: {response.status_code}")
            print(f"  📄 Respuesta: {response.text[:200]}")
            
    except requests.exceptions.ConnectTimeout:
        print(f"  ⏱️ Timeout de conexión")
    except requests.exceptions.ConnectionError as e:
        print(f"  🚫 Error de conexión: {str(e)[:100]}...")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}...")
    
    return False, None

def diagnose_ollama_server():
    """Diagnóstico completo del servidor Ollama UPV"""
    
    host = "ollama.gti-ia.upv.es"
    print(f"🔧 DIAGNÓSTICO SERVIDOR OLLAMA UPV: {host}")
    print("=" * 60)
    
    # 1. Prueba conectividad básica
    print("\n1️⃣ PRUEBA DE CONECTIVIDAD BÁSICA")
    print("-" * 40)
    
    common_ports = [80, 443, 8080, 8000, 3000, 11434]
    open_ports = []
    
    for port in common_ports:
        if test_port_connectivity(host, port):
            print(f"  ✅ Puerto {port}: ABIERTO")
            open_ports.append(port)
        else:
            print(f"  ❌ Puerto {port}: CERRADO/INACCESIBLE")
    
    if not open_ports:
        print(f"\n🚨 PROBLEMA: Ningún puerto común está accesible en {host}")
        print("   Posibles causas:")
        print("   - VPN no conectada correctamente")
        print("   - Servidor apagado o no accesible")
        print("   - Firewall bloqueando conexiones")
        print("   - Dirección incorrecta")
        return
    
    # 2. Prueba HTTPS
    print(f"\n2️⃣ PRUEBA HTTPS")
    print("-" * 40)
    if test_https_connectivity(host):
        print(f"  ✅ HTTPS disponible en {host}:443")
    else:
        print(f"  ❌ HTTPS no disponible")
    
    # 3. Prueba diferentes configuraciones de Ollama
    print(f"\n3️⃣ PRUEBA ENDPOINTS OLLAMA")
    print("-" * 40)
    
    # Configuraciones a probar
    test_configs = [
        # HTTP en puertos comunes
        f"http://{host}:11434",  # Puerto por defecto Ollama
        f"http://{host}:8080",   # Puerto web alternativo
        f"http://{host}:80",     # Puerto HTTP estándar
        f"http://{host}",        # Sin puerto (puerto 80 implícito)
        
        # HTTPS en puertos comunes  
        f"https://{host}:443",   # Puerto HTTPS estándar
        f"https://{host}",       # Sin puerto (puerto 443 implícito)
        f"https://{host}:8080",  # HTTPS en puerto alternativo
    ]
    
    working_configs = []
    
    for config in test_configs:
        success, data = test_ollama_endpoint(config)
        if success:
            working_configs.append((config, data))
    
    # 4. Resultados
    print(f"\n4️⃣ RESULTADOS")
    print("=" * 60)
    
    if working_configs:
        print("🎉 ¡CONFIGURACIONES QUE FUNCIONAN!")
        for config, data in working_configs:
            print(f"\n✅ FUNCIONA: {config}")
            if data and 'models' in data:
                models = data['models']
                print(f"   📊 Modelos disponibles: {len(models)}")
                for model in models[:3]:  # Mostrar solo primeros 3
                    name = model.get('name', 'Unknown')
                    size = model.get('size', 0) / (1024**3)
                    print(f"      - {name} ({size:.1f}GB)")
                if len(models) > 3:
                    print(f"      ... y {len(models)-3} más")
        
        # Generar código de ejemplo
        best_config = working_configs[0][0]
        print(f"\n💡 CÓDIGO PARA TU APLICACIÓN:")
        print("-" * 40)
        print(f"""
# Usar esta configuración en tu código:
from spade_llm.providers import LLMProvider

provider = LLMProvider.create_ollama(
    model="llama3:8b",  # O el modelo que quieras usar
    base_url="{best_config}/v1",  # Nota el /v1 al final
    timeout=120.0
)
        """)
        
    else:
        print("🚨 NO SE ENCONTRÓ NINGUNA CONFIGURACIÓN QUE FUNCIONE")
        print("\n💡 PRÓXIMOS PASOS:")
        print("   1. Verifica que estás conectado a la VPN UPV")
        print("   2. Contacta al administrador del servidor")
        print("   3. Verifica la dirección del servidor")
        if open_ports:
            print(f"   4. El servidor responde en puerto(s): {', '.join(map(str, open_ports))}")
            print("      Puede que use un endpoint diferente a /api/tags")

if __name__ == "__main__":
    diagnose_ollama_server()

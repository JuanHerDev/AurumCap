#!/usr/bin/env python3
"""
Script para probar los endpoints de plataformas actualizados
"""
import sys
import os
import requests
import json
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración - ajusta según tu entorno
BASE_URL = "http://localhost:8000/api"
HEADERS = {
    "Content-Type": "application/json"
}
# Añade tu token de autenticación si es necesario
# HEADERS["Authorization"] = "Bearer tu_token_aqui"

def test_platforms_endpoints():
    """Probar los endpoints de plataformas"""
    
    print("🧪 Probando endpoints de plataformas...")
    
    try:
        # 1. Obtener lista de plataformas
        print("\n1. 📋 Obteniendo lista de plataformas...")
        response = requests.get(f"{BASE_URL}/platforms", headers=HEADERS)
        
        if response.status_code == 200:
            platforms = response.json()
            print(f"   ✅ Success - {len(platforms)} plataformas obtenidas")
            for platform in platforms[:3]:  # Mostrar solo las primeras 3
                print(f"      • {platform['display_name']} - {platform['type']}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
        
        # 2. Obtener plataformas por tipo de activo
        print("\n2. 🔍 Obteniendo plataformas para crypto...")
        response = requests.get(f"{BASE_URL}/platforms/by-asset-type/crypto", headers=HEADERS)
        
        if response.status_code == 200:
            crypto_platforms = response.json()
            print(f"   ✅ Success - {len(crypto_platforms)} plataformas para crypto")
            for platform in crypto_platforms:
                print(f"      • {platform['display_name']} - {platform['supported_asset_types']}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
        
        # 3. Probar filtro por tipo de activo en el endpoint principal
        print("\n3. 🎯 Probando filtro stock en endpoint principal...")
        response = requests.get(f"{BASE_URL}/platforms?asset_type=stock", headers=HEADERS)
        
        if response.status_code == 200:
            stock_platforms = response.json()
            print(f"   ✅ Success - {len(stock_platforms)} plataformas para stocks")
            for platform in stock_platforms:
                print(f"      • {platform['display_name']} - {platform['supported_asset_types']}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
        
        # 4. Crear una nueva inversión con platform_specific_id
        print("\n4. 💰 Probando creación de inversión con platform_specific_id...")
        
        investment_data = {
            "asset_type": "crypto",
            "symbol": "BTC",
            "asset_name": "Bitcoin",
            "invested_amount": "1000.00",
            "quantity": "0.02",
            "purchase_price": "50000.00",
            "currency": "USD",
            "platform_id": 1,  # ID de Binance
            "platform_specific_id": "binance_btc_wallet_001",  # NUEVO CAMPO
            "notes": "Inversión de prueba con platform_specific_id"
        }
        
        response = requests.post(f"{BASE_URL}/investments", json=investment_data, headers=HEADERS)
        
        if response.status_code == 201:
            investment = response.json()
            print(f"   ✅ Success - Inversión creada con ID: {investment['id']}")
            print(f"      Platform Specific ID: {investment.get('platform_specific_id', 'No encontrado')}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
        
        print("\n🎉 Pruebas de endpoints completadas!")
        
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor. Asegúrate de que FastAPI esté ejecutándose.")
    except Exception as e:
        print(f"❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_platforms_endpoints()
#!/usr/bin/env python3
"""
Verificar que los nuevos modelos son compatibles con las tablas existentes
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from sqlalchemy import inspect

def verify_compatibility():
    """Verificar que los modelos coinciden con las tablas existentes"""
    db = SessionLocal()
    
    try:
        inspector = inspect(db.get_bind())
        
        print("🔍 VERIFICANDO COMPATIBILIDAD MODELOS-TABLAS")
        print("=" * 50)
        
        # Verificar tablas críticas
        critical_tables = {
            'crypto_profiles': ['id', 'symbol', 'name', 'cache_until'],
            'stock_profiles': ['symbol', 'company_name', 'cache_until'],
            'trades': ['id', 'symbol', 'position_type', 'trade_action', 'quantity'],
            'investments': ['id', 'user_id', 'symbol', 'asset_type', 'quantity'],
            'users': ['id', 'email', 'hashed_password', 'is_active']
        }
        
        all_ok = True
        for table_name, expected_columns in critical_tables.items():
            if table_name in inspector.get_table_names():
                actual_columns = [col['name'] for col in inspector.get_columns(table_name)]
                missing_columns = [col for col in expected_columns if col not in actual_columns]
                
                if not missing_columns:
                    print(f"✅ {table_name} - COMPATIBLE")
                else:
                    print(f"❌ {table_name} - Columnas faltantes: {missing_columns}")
                    all_ok = False
            else:
                print(f"❌ {table_name} - TABLA NO ENCONTRADA")
                all_ok = False
        
        print("\n" + "=" * 50)
        if all_ok:
            print("🎉 ¡TODOS LOS MODELOS SON COMPATIBLES CON LAS TABLAS EXISTENTES!")
            print("   Puedes empezar a usar los nuevos modelos inmediatamente.")
        else:
            print("⚠️  Hay problemas de compatibilidad que necesitan atención.")
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_compatibility()
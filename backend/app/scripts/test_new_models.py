#!/usr/bin/env python3
"""
Probar que los nuevos modelos funcionan con las tablas existentes
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal

def test_new_models():
    """Probar consultas básicas con los nuevos modelos"""
    db = SessionLocal()
    
    try:
        print("🧪 PROBANDO NUEVOS MODELOS CON TABLAS EXISTENTES")
        print("=" * 40)
        
        # Importar los nuevos modelos
        from app.models.crypto.crypto_models import CryptoProfile
        from app.models.stocks.stock_models import StockProfile
        from app.models.trading.trading_models import Trade
        from app.models.investment import Investment
        from app.models.user import User
        
        # Probar consultas básicas
        try:
            crypto_count = db.query(CryptoProfile).count()
            print(f"✅ CryptoProfile: {crypto_count} registros")
        except Exception as e:
            print(f"❌ CryptoProfile: Error - {e}")
        
        try:
            stock_count = db.query(StockProfile).count() 
            print(f"✅ StockProfile: {stock_count} registros")
        except Exception as e:
            print(f"❌ StockProfile: Error - {e}")
        
        try:
            trades_count = db.query(Trade).count()
            print(f"✅ Trade: {trades_count} registros")
        except Exception as e:
            print(f"❌ Trade: Error - {e}")
            
        try:
            investments_count = db.query(Investment).count()
            print(f"✅ Investment: {investments_count} registros")
        except Exception as e:
            print(f"❌ Investment: Error - {e}")
            
        try:
            users_count = db.query(User).count()
            print(f"✅ User: {users_count} registros")
        except Exception as e:
            print(f"❌ User: Error - {e}")
        
        print("\n🎉 ¡PRUEBAS COMPLETADAS!")
        
    except Exception as e:
        print(f"❌ Error general probando modelos: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_new_models()
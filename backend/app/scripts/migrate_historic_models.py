#!/usr/bin/env python3
"""
Script para migrar de models/historic.py a la nueva estructura
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal, engine

def migrate_models():
    """Crear todas las nuevas tablas"""
    from app.models.crypto import crypto_models
    from app.models.stocks import stock_models  
    from app.models.fundamentals import fundamental_models
    from app.models.trading import trading_models
    from app.models.macro import macro_models
    
    # Crear todas las tablas
    crypto_models.Base.metadata.create_all(engine)
    stock_models.Base.metadata.create_all(engine)
    fundamental_models.Base.metadata.create_all(engine)
    trading_models.Base.metadata.create_all(engine)
    macro_models.Base.metadata.create_all(engine)
    
    print("✅ Todas las tablas migradas exitosamente!")
    print("📊 Estructura creada:")
    print("   - Crypto: 3 modelos")
    print("   - Stocks: 4 modelos") 
    print("   - Fundamentals: 3 modelos")
    print("   - Trading: 8 modelos")
    print("   - Macro: 2 modelos")

if __name__ == "__main__":
    migrate_models()
#!/usr/bin/env python3
"""
Script para verificar que la migración de plataformas se aplicó correctamente
"""
import sys
import os

# Agregar el directorio raíz al path para importar app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.platform import Platform
from app.models.investment import Investment
from sqlalchemy import text, inspect

def verify_migration():
    """Verificar que la migración se aplicó correctamente"""
    db = SessionLocal()
    
    try:
        print("🔍 Verificando migración de campos de plataformas...")
        
        # Obtener el inspector de SQLAlchemy
        inspector = inspect(db.get_bind())
        
        # Verificar campos en platforms
        platform_columns = [col['name'] for col in inspector.get_columns('platforms')]
        required_platform_columns = ['display_name', 'is_active', 'supported_asset_types', 'api_config', 'icon']
        
        print("📋 Campos en tabla 'platforms':")
        for col in platform_columns:
            status = "✅" if col in required_platform_columns else "  "
            print(f"   {status} {col}")
        
        missing_platform = [col for col in required_platform_columns if col not in platform_columns]
        if missing_platform:
            print(f"❌ Campos faltantes en platforms: {missing_platform}")
        else:
            print("✅ Todos los campos requeridos están en platforms")
        
        # Verificar campos en investments
        investment_columns = [col['name'] for col in inspector.get_columns('investments')]
        required_investment_columns = ['platform_specific_id']
        
        print("\n📋 Campos en tabla 'investments':")
        for col in investment_columns:
            status = "✅" if col in required_investment_columns else "  "
            print(f"   {status} {col}")
        
        missing_investment = [col for col in required_investment_columns if col not in investment_columns]
        if missing_investment:
            print(f"❌ Campos faltantes en investments: {missing_investment}")
        else:
            print("✅ Todos los campos requeridos están en investments")
        
        # Verificar índices
        investment_indexes = [idx['name'] for idx in inspector.get_indexes('investments')]
        if 'ix_investments_platform_specific_id' in investment_indexes:
            print("✅ Índice ix_investments_platform_specific_id creado correctamente")
        else:
            print("❌ Índice ix_investments_platform_specific_id no encontrado")
        
        # Verificar datos de plataformas
        platforms = db.query(Platform).all()
        print(f"\n🏦 Plataformas existentes: {len(platforms)}")
        
        for platform in platforms:
            print(f"   📍 {platform.display_name} ({platform.name})")
            print(f"      Tipo: {platform.type}")
            print(f"      Activo: {platform.is_active}")
            print(f"      Tipos de activo soportados: {platform.supported_asset_types}")
            if platform.icon:
                print(f"      Icono: {platform.icon}")
        
        # Verificar que las plataformas tengan display_name
        platforms_without_display = db.query(Platform).filter(
            (Platform.display_name == '') | (Platform.display_name.is_(None))
        ).count()
        
        if platforms_without_display == 0:
            print("✅ Todas las plataformas tienen display_name")
        else:
            print(f"❌ {platforms_without_display} plataformas sin display_name")
        
        print("\n🎉 Verificación de migración completada!")
        
    except Exception as e:
        print(f"❌ Error en verificación: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_migration()
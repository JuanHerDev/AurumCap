#!/usr/bin/env python3
"""
Script para poblar las plataformas por defecto después de la migración
"""
import sys
import os

# Agregar el directorio raíz al path para importar app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.platform import Platform, PlatformType

def seed_default_platforms():
    """Poblar plataformas por defecto"""
    db = SessionLocal()
    
    try:
        print("🌱 Sembrando plataformas por defecto...")
        
        default_platforms = [
            {
                "name": "binance",
                "display_name": "Binance",
                "type": PlatformType.exchange,
                "description": "Global cryptocurrency exchange",
                "supported_asset_types": ["crypto"],
                "icon": "binance-icon.png",
                "is_active": True
            },
            {
                "name": "coinbase",
                "display_name": "Coinbase", 
                "type": PlatformType.exchange,
                "description": "US-based cryptocurrency exchange",
                "supported_asset_types": ["crypto"],
                "icon": "coinbase-icon.png",
                "is_active": True
            },
            {
                "name": "interactive_brokers",
                "display_name": "Interactive Brokers",
                "type": PlatformType.broker,
                "description": "International brokerage platform",
                "supported_asset_types": ["stock", "etf", "bond"],
                "icon": "ib-icon.png",
                "is_active": True
            },
            {
                "name": "etoro",
                "display_name": "eToro", 
                "type": PlatformType.broker,
                "description": "Social trading and investment platform",
                "supported_asset_types": ["stock", "crypto", "etf"],
                "icon": "etoro-icon.png",
                "is_active": True
            },
            {
                "name": "metamask",
                "display_name": "Metamask",
                "type": PlatformType.wallet,
                "description": "Cryptocurrency wallet and DeFi gateway",
                "supported_asset_types": ["crypto"],
                "icon": "metamask-icon.png",
                "is_active": True
            },
            {
                "name": "ledger",
                "display_name": "Ledger",
                "type": PlatformType.wallet,
                "description": "Hardware cryptocurrency wallet",
                "supported_asset_types": ["crypto"],
                "icon": "ledger-icon.png",
                "is_active": True
            },
            {
                "name": "other",
                "display_name": "Other", 
                "type": PlatformType.other,
                "description": "Other platform or manual entry",
                "supported_asset_types": ["stock", "crypto", "etf", "bond", "real_estate", "other"],
                "icon": "other-icon.png",
                "is_active": True
            }
        ]
        
        platforms_created = 0
        platforms_updated = 0
        
        for platform_data in default_platforms:
            # Verificar si la plataforma ya existe
            existing = db.query(Platform).filter(Platform.name == platform_data["name"]).first()
            
            if not existing:
                # Crear nueva plataforma
                platform = Platform(**platform_data)
                db.add(platform)
                platforms_created += 1
                print(f"  ✅ Creada: {platform_data['display_name']}")
            else:
                # Actualizar plataforma existente
                for key, value in platform_data.items():
                    if hasattr(existing, key) and key != 'name':  # No actualizar el nombre
                        setattr(existing, key, value)
                platforms_updated += 1
                print(f"  🔄 Actualizada: {platform_data['display_name']}")
        
        db.commit()
        
        print(f"\n📊 Resumen de siembra:")
        print(f"   📈 Plataformas creadas: {platforms_created}")
        print(f"   🔄 Plataformas actualizadas: {platforms_updated}")
        print(f"   📦 Total procesadas: {len(default_platforms)}")
        
        # Verificar el resultado final
        total_platforms = db.query(Platform).count()
        print(f"   🏦 Total de plataformas en BD: {total_platforms}")
        
        print("🎉 Siembra de plataformas completada!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la siembra: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_default_platforms()
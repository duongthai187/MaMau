"""
Business services layer
"""
from .gold_attribute_service import OdooGoldAttributeService
from .pricing_service import PricingCalculator
from .kafka_service import KafkaPricingConsumer

# Create service instances
gold_attribute_service = OdooGoldAttributeService()

__all__ = [
    'OdooGoldAttributeService',
    'PricingCalculator', 
    'KafkaPricingConsumer',
    'gold_attribute_service'
]

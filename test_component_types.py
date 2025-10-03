#!/usr/bin/env python3
"""
Test script to check component type enum values
"""

import sys
import os
sys.path.append('/Users/spero/Desktop/HRP4')

from app.models.payroll import SalaryComponentType

def test_component_types():
    """Test component type enum values"""
    print("🔍 Testing Component Type Enums")
    print("=" * 50)
    
    print("\n📋 Available Component Types:")
    for component_type in SalaryComponentType:
        print(f"   {component_type.name} = '{component_type.value}'")
    
    print("\n🎯 Testing specific types used in payroll:")
    test_types = [
        'HOUSING_ALLOWANCE',
        'TRANSPORT_ALLOWANCE', 
        'MEDICAL_ALLOWANCE',
        'MEAL_ALLOWANCE',
        'LOAN_DEDUCTION',
        'ADVANCE_DEDUCTION',
        'UNIFORM_DEDUCTION',
        'PARKING_DEDUCTION',
        'LATE_PENALTY'
    ]
    
    for type_name in test_types:
        try:
            component_type = getattr(SalaryComponentType, type_name)
            print(f"   ✅ {type_name}: {component_type.value}")
        except AttributeError:
            print(f"   ❌ {type_name}: NOT FOUND")
    
    print("\n🎉 Component type test completed!")

if __name__ == "__main__":
    test_component_types()

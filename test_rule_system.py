"""
Test script for the Rule Engine system
测试规则引擎功能
"""

import sys
import json
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append('.')

def test_rule_engine_basic():
    """测试规则引擎基本功能"""
    print("🧪 Testing Rule Engine Basic Functionality")
    print("=" * 50)
    
    try:
        from core.rule_engine import rule_engine
        
        # Test rule registration
        print(f"✅ Rule engine loaded successfully")
        print(f"📊 Total rules registered: {len(rule_engine.rules)}")
        
        # List all rules
        print("\n📋 Registered Rules:")
        for rule_id, rule in rule_engine.rules.items():
            print(f"  • {rule_id} ({rule.category.value}) - Priority: {rule.priority}")
            print(f"    Description: {rule.get_description()}")
            print(f"    Enabled: {rule.enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Rule engine test failed: {e}")
        return False


def test_world_initialization():
    """测试世界初始化和规则集成"""
    print("\n🌍 Testing World Initialization with Rules")
    print("=" * 50)
    
    try:
        from core.world import World
        from core.clock import TimeController
        from core.rule_engine import rule_engine
        
        # Initialize world
        world = World()
        world.initialize_world(guard_count=2, prisoner_count=4)
        
        print(f"✅ World initialized successfully")
        print(f"🏛️ Map size: {world.state.game_map.width}x{world.state.game_map.height}")
        print(f"👮 Guards: {len([a for a in world.state.agents.values() if a.role.value == 'Guard'])}")
        print(f"🔒 Prisoners: {len([a for a in world.state.agents.values() if a.role.value == 'Prisoner'])}")
        
        # Test time advancement and rule execution
        clock = TimeController()
        
        print(f"\n⏰ Initial time: Day {world.state.day}, Hour {world.state.hour}")
        
        # Advance time to trigger rules
        print("\n🔄 Advancing time to test rule triggers...")
        
        # Test multiple time advances
        for i in range(3):
            old_hour = world.state.hour
            clock.advance_time(world.state)
            new_hour = world.state.hour
            
            print(f"  Time advanced: Day {world.state.day}, Hour {world.state.hour}")
            
            # Check if any rules were executed
            recent_events = [event for event in world.state.event_log if "[RULE]" in event]
            if recent_events:
                print(f"  📜 Rule events triggered:")
                for event in recent_events[-3:]:  # Show last 3 rule events
                    print(f"    {event}")
        
        return True
        
    except Exception as e:
        print(f"❌ World initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_food_distribution_rules():
    """测试食物分发规则"""
    print("\n🍽️ Testing Food Distribution Rules")
    print("=" * 50)
    
    try:
        from core.world import World
        from core.clock import TimeController
        from core.rule_engine import rule_engine
        
        # Initialize world
        world = World()
        world.initialize_world(guard_count=2, prisoner_count=4)
        clock = TimeController()
        
        # Set time to trigger guard food distribution (8:00)
        world.state.hour = 8
        world.state.minute = 0
        
        print(f"⏰ Set time to trigger food distribution: Day {world.state.day}, Hour {world.state.hour}:00")
        
        # Count initial guard inventory
        guards = [agent for agent in world.state.agents.values() if agent.role.value == "Guard"]
        initial_food_counts = {}
        for guard in guards:
            food_count = len([item for item in guard.inventory if item.item_type.value == "food"])
            initial_food_counts[guard.agent_id] = food_count
            print(f"  🥘 {guard.name} initial food items: {food_count}")
        
        # Execute rule
        print(f"\n🔄 Executing rules at {world.state.hour}:00...")
        rule_events = rule_engine.execute_rules(world.state)
        
        if rule_events:
            print(f"📜 Rule events executed:")
            for event in rule_events:
                print(f"  {event}")
        
        # Check guard inventory after rule execution
        print(f"\n📊 Guard inventories after rule execution:")
        for guard in guards:
            food_count = len([item for item in guard.inventory if item.item_type.value == "food"])
            water_count = len([item for item in guard.inventory if item.item_type.value == "water"])
            food_gained = food_count - initial_food_counts[guard.agent_id]
            print(f"  🥘 {guard.name}: {food_count} food (+{food_gained}), {water_count} water")
        
        return True
        
    except Exception as e:
        print(f"❌ Food distribution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cafeteria_supply_rules():
    """测试食堂供应规则"""
    print("\n🏪 Testing Cafeteria Supply Rules")
    print("=" * 50)
    
    try:
        from core.world import World
        from core.clock import TimeController
        from core.rule_engine import rule_engine
        
        # Initialize world
        world = World()
        world.initialize_world(guard_count=2, prisoner_count=4)
        clock = TimeController()
        
        # Find cafeteria position
        cafeteria_pos = None
        for pos, cell_type in world.state.game_map.cells.items():
            if cell_type.value == "Cafeteria":
                cafeteria_pos = pos
                break
        
        if cafeteria_pos:
            print(f"🏪 Cafeteria found at position: {cafeteria_pos}")
            
            # Check initial cafeteria items
            initial_items = world.state.game_map.items.get(cafeteria_pos, [])
            print(f"  📦 Initial items in cafeteria: {len(initial_items)}")
            
            # Set time to trigger cafeteria supply (7:00 breakfast)
            world.state.hour = 7
            world.state.minute = 0
            
            print(f"\n⏰ Set time to trigger breakfast supply: Day {world.state.day}, Hour {world.state.hour}:00")
            
            # Execute rule
            rule_events = rule_engine.execute_rules(world.state)
            
            if rule_events:
                print(f"📜 Cafeteria supply events:")
                for event in rule_events:
                    print(f"  {event}")
            
            # Check cafeteria items after rule execution
            after_items = world.state.game_map.items.get(cafeteria_pos, [])
            food_items = [item for item in after_items if item.item_type.value == "food"]
            water_items = [item for item in after_items if item.item_type.value == "water"]
            
            print(f"\n📊 Cafeteria inventory after supply:")
            print(f"  🥘 Food items: {len(food_items)}")
            print(f"  💧 Water items: {len(water_items)}")
            
            # Show item details
            if food_items:
                print(f"  📝 Food items details:")
                for item in food_items[:3]:  # Show first 3
                    print(f"    • {item.name} (ID: {item.item_id})")
            
        else:
            print("❌ Cafeteria not found in map")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Cafeteria supply test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rule_api_integration():
    """测试规则API集成"""
    print("\n🔌 Testing Rule API Integration")
    print("=" * 50)
    
    try:
        from api.rule_management import get_rule_engine_status, list_all_rules
        import asyncio
        
        # Test status endpoint
        print("📊 Testing rule engine status API...")
        status = asyncio.run(get_rule_engine_status())
        print(f"  ✅ Status API response: {status['success']}")
        print(f"  📈 Total rules: {status['data']['total_rules']}")
        print(f"  🟢 Enabled rules: {status['data']['enabled_rules']}")
        
        # Test rule list endpoint
        print("\n📋 Testing rule list API...")
        rules_list = asyncio.run(list_all_rules())
        print(f"  ✅ Retrieved {len(rules_list)} rules")
        
        for rule in rules_list[:3]:  # Show first 3 rules
            print(f"    • {rule.rule_id} ({rule.category}) - Enabled: {rule.enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Rule API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rule_configuration():
    """测试规则配置系统"""
    print("\n⚙️ Testing Rule Configuration System")
    print("=" * 50)
    
    try:
        # Test configuration loading
        with open('configs/game_rules.json', 'r') as f:
            config = json.load(f)
        
        print("✅ Game rules configuration loaded")
        
        # Check if new rule engine config exists
        if "rule_engine" in config:
            print("✅ Rule engine configuration found")
            rule_config = config["rule_engine"]
            print(f"  🔧 Enabled: {rule_config.get('enabled', False)}")
            print(f"  📊 Max rules per turn: {rule_config.get('max_rules_per_turn', 0)}")
            print(f"  🐛 Debug mode: {rule_config.get('debug_mode', False)}")
        
        # Check food distribution rules config
        if "food_distribution_rules" in config:
            print("✅ Food distribution rules configuration found")
            food_config = config["food_distribution_rules"]
            
            guard_supply = food_config.get("guard_automatic_supply", {})
            print(f"  👮 Guard supply enabled: {guard_supply.get('enabled', False)}")
            print(f"  ⏰ Guard supply schedule: {guard_supply.get('schedule', [])}")
            
            cafeteria_supply = food_config.get("cafeteria_supply", {})
            print(f"  🏪 Cafeteria supply enabled: {cafeteria_supply.get('enabled', False)}")
            print(f"  📉 Scarcity factor: {cafeteria_supply.get('scarcity_factor', 1.0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def main():
    """运行所有测试"""
    print("🚀 Project Prometheus - Rule Engine Test Suite")
    print("=" * 60)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Basic Rule Engine", test_rule_engine_basic),
        ("World Initialization", test_world_initialization),
        ("Food Distribution Rules", test_food_distribution_rules),
        ("Cafeteria Supply Rules", test_cafeteria_supply_rules),
        ("Rule Configuration", test_rule_configuration),
        ("Rule API Integration", test_rule_api_integration),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Rule engine is ready for use.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    main()
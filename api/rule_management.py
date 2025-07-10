"""
Rule Management API for Project Prometheus
Runtime rule control and monitoring endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from core.rule_engine import rule_engine, RuleCategory

router = APIRouter(prefix="/rules", tags=["rule_management"])


class RuleConfigUpdate(BaseModel):
    """规则配置更新模型"""
    rule_id: str
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None


class RuleStatus(BaseModel):
    """规则状态模型"""
    rule_id: str
    category: str
    enabled: bool
    priority: int
    description: str
    last_execution: Optional[str] = None


@router.get("/status", response_model=Dict[str, Any])
async def get_rule_engine_status():
    """获取规则引擎状态"""
    try:
        status = rule_engine.get_rule_status()
        return {
            "success": True,
            "data": status,
            "message": "Rule engine status retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rule status: {str(e)}")


@router.get("/list", response_model=List[RuleStatus])
async def list_all_rules():
    """列出所有规则"""
    try:
        rules_info = []
        descriptions = rule_engine.get_rule_descriptions()
        
        for rule_id, rule in rule_engine.rules.items():
            # 查找最近执行记录
            last_execution = None
            for history in reversed(rule_engine.rule_history):
                if history["rule_id"] == rule_id:
                    last_execution = history["timestamp"]
                    break
            
            rules_info.append(RuleStatus(
                rule_id=rule_id,
                category=rule.category.value,
                enabled=rule.enabled,
                priority=rule.priority,
                description=descriptions.get(rule_id, "No description available"),
                last_execution=last_execution
            ))
        
        return rules_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list rules: {str(e)}")


@router.post("/enable/{rule_id}")
async def enable_rule(rule_id: str):
    """启用规则"""
    try:
        if rule_id not in rule_engine.rules:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        rule_engine.enable_rule(rule_id)
        return {
            "success": True,
            "message": f"Rule {rule_id} enabled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable rule: {str(e)}")


@router.post("/disable/{rule_id}")
async def disable_rule(rule_id: str):
    """禁用规则"""
    try:
        if rule_id not in rule_engine.rules:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        rule_engine.disable_rule(rule_id)
        return {
            "success": True,
            "message": f"Rule {rule_id} disabled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable rule: {str(e)}")


@router.get("/history")
async def get_rule_execution_history(limit: int = 50):
    """获取规则执行历史"""
    try:
        history = rule_engine.rule_history[-limit:] if rule_engine.rule_history else []
        return {
            "success": True,
            "data": {
                "history": list(reversed(history)),  # 最新的在前
                "total_executions": len(rule_engine.rule_history)
            },
            "message": f"Retrieved last {len(history)} rule executions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rule history: {str(e)}")


@router.get("/categories")
async def get_rule_categories():
    """获取规则分类信息"""
    try:
        categories_info = {}
        for category in RuleCategory:
            category_rules = [
                rule_id for rule_id, rule in rule_engine.rules.items()
                if rule.category == category
            ]
            categories_info[category.value] = {
                "total_rules": len(category_rules),
                "enabled_rules": len([
                    rule_id for rule_id in category_rules
                    if rule_engine.rules[rule_id].enabled
                ]),
                "rule_ids": category_rules
            }
        
        return {
            "success": True,
            "data": categories_info,
            "message": "Rule categories retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rule categories: {str(e)}")


@router.post("/test/{rule_id}")
async def test_rule_trigger(rule_id: str):
    """测试规则触发条件（仅检查，不执行）"""
    try:
        if rule_id not in rule_engine.rules:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        from core.world import World
        world = World()
        
        if not world.state:
            raise HTTPException(status_code=400, detail="World state not initialized")
        
        rule = rule_engine.rules[rule_id]
        will_trigger = rule.check_trigger(world.state)
        
        return {
            "success": True,
            "data": {
                "rule_id": rule_id,
                "will_trigger": will_trigger,
                "current_time": f"Day {world.state.day} Hour {world.state.hour}",
                "rule_enabled": rule.enabled
            },
            "message": f"Rule {rule_id} trigger test completed"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test rule: {str(e)}")


@router.get("/food-distribution/status")
async def get_food_distribution_status():
    """获取食物分发规则状态"""
    try:
        food_rules = {
            "guard_food_distribution": rule_engine.rules.get("guard_food_distribution"),
            "cafeteria_food_supply": rule_engine.rules.get("cafeteria_food_supply"),
            "food_scarcity": rule_engine.rules.get("food_scarcity")
        }
        
        status = {}
        for rule_id, rule in food_rules.items():
            if rule:
                status[rule_id] = {
                    "enabled": rule.enabled,
                    "priority": rule.priority,
                    "category": rule.category.value,
                    "description": rule.get_description()
                }
            else:
                status[rule_id] = {"status": "not_found"}
        
        return {
            "success": True,
            "data": status,
            "message": "Food distribution rules status retrieved"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get food distribution status: {str(e)}")


@router.post("/food-distribution/configure")
async def configure_food_distribution(config: Dict[str, Any]):
    """配置食物分发规则参数"""
    try:
        # 这里可以实现动态配置更新
        # 目前返回配置接收确认
        return {
            "success": True,
            "data": {
                "received_config": config,
                "applied": False,
                "note": "Dynamic rule reconfiguration not yet implemented"
            },
            "message": "Configuration received (implementation pending)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure food distribution: {str(e)}")


@router.get("/debug/next-triggers")
async def get_next_rule_triggers():
    """获取接下来会触发的规则（调试用）"""
    try:
        from core.world import World
        world = World()
        
        if not world.state:
            raise HTTPException(status_code=400, detail="World state not initialized")
        
        next_triggers = []
        current_hour = world.state.hour
        
        # 检查接下来24小时内的触发情况
        for hour_offset in range(24):
            test_hour = (current_hour + hour_offset) % 24
            test_day = world.state.day + (current_hour + hour_offset) // 24
            
            for rule_id, rule in rule_engine.rules.items():
                if rule.enabled and hasattr(rule, 'trigger_hours'):
                    if test_hour in rule.trigger_hours:
                        next_triggers.append({
                            "rule_id": rule_id,
                            "trigger_time": f"Day {test_day} Hour {test_hour}:00",
                            "hours_from_now": hour_offset,
                            "category": rule.category.value
                        })
        
        # 按时间排序
        next_triggers.sort(key=lambda x: x["hours_from_now"])
        
        return {
            "success": True,
            "data": {
                "current_time": f"Day {world.state.day} Hour {current_hour}:00",
                "next_triggers": next_triggers[:10]  # 只返回前10个
            },
            "message": "Next rule triggers calculated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate next triggers: {str(e)}")
"""
分支规则管理 API

包含以下功能：
- 分支规则 CRUD 操作
- 规则模式测试
- 规则应用到分支
- 分支删除报告生成和导出
"""

from flask import Blueprint, send_file, jsonify
from datetime import datetime
from dataclasses import asdict
from services.branch_rule_service import BranchRuleService
from services.export_service import ExportService
from api.response import api_response
from utils.validators import validate_json_request, get_request_params
from utils.errorhandler import handle_exceptions

branch_rule_bp = Blueprint('branch_rule', __name__)


@branch_rule_bp.route('', methods=['GET'])
@handle_exceptions
def get_branch_rules():
    """获取所有分支规则"""
    params = get_request_params({
        'include_inactive': {'default': 'true'}
    })
    
    include_inactive = params['include_inactive'].lower() == 'true'
    
    rule_service = BranchRuleService()
    rules = rule_service.get_all_rules(include_inactive)
    
    # 将 BranchRuleData 对象转换为字典
    rules_dict = [asdict(rule) for rule in rules]
    
    return api_response(
        rules=rules_dict,
        count=len(rules_dict)
    )


@branch_rule_bp.route('', methods=['POST'])
@handle_exceptions
@validate_json_request(['rule_name', 'branch_pattern', 'branch_type'])
def create_branch_rule(validated_data):
    """创建新的分支规则"""
    rule_service = BranchRuleService()
    result = rule_service.create_rule(validated_data)
    
    status_code = 201 if result.get('success', True) else 400
    return jsonify(result), status_code


@branch_rule_bp.route('/<int:rule_id>', methods=['GET'])
@handle_exceptions
def get_branch_rule(rule_id):
    """获取单个分支规则""" 
    rule_service = BranchRuleService()
    rule = rule_service.get_rule_by_id(rule_id)
    
    if rule:
        return api_response(rule=asdict(rule))
    else:
        return api_response(success=False, error='Rule not found', status_code=404)


@branch_rule_bp.route('/<int:rule_id>', methods=['PUT'])
@handle_exceptions
@validate_json_request()
def update_branch_rule(rule_id, validated_data):
    """更新分支规则"""
    rule_service = BranchRuleService()
    result = rule_service.update_rule(rule_id, validated_data)
    
    status_code = 200 if result.get('success', True) else 400
    return jsonify(result), status_code


@branch_rule_bp.route('/<int:rule_id>', methods=['DELETE'])
@handle_exceptions
def delete_branch_rule(rule_id):
    """删除分支规则"""
    rule_service = BranchRuleService()
    result = rule_service.delete_rule(rule_id)
    
    status_code = 200 if result.get('success', True) else 400
    return jsonify(result), status_code


@branch_rule_bp.route('/test-pattern', methods=['POST'])
@handle_exceptions
@validate_json_request(['pattern'])
def test_rule_pattern(validated_data):
    """测试规则模式匹配"""
    pattern = validated_data['pattern']
    test_branches = validated_data.get('test_branches', [])
    
    rule_service = BranchRuleService()
    result = rule_service.test_rule_pattern(pattern, test_branches)
    
    return jsonify(result)


@branch_rule_bp.route('/apply', methods=['POST'])
@handle_exceptions
def apply_branch_rules():
    """应用分支规则到所有分支"""
    params = get_request_params({
        'repository_id': {'type': int, 'required': False}
    })
    
    rule_service = BranchRuleService()
    result = rule_service.apply_rules_to_branches(params['repository_id'])
    
    status_code = 200 if result.get('success', True) else 500
    return jsonify(result), status_code


@branch_rule_bp.route('/deletion-report/excel', methods=['GET'])
@handle_exceptions
def export_branch_deletion_report_excel():
    """导出分支删除报告为 Excel 文件"""
    params = get_request_params({
        'repository_id': {'type': int, 'required': False}
    })
    
    export_service = ExportService()
    excel_buffer = export_service.export_branch_deletion_report_to_excel(params['repository_id'])
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"分支删除报告_{timestamp}.xlsx"
    
    if params['repository_id']:
        filename = f"分支删除报告_仓库{params['repository_id']}_{timestamp}.xlsx"
    
    return send_file(
        excel_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@branch_rule_bp.route('/deletion-report', methods=['GET'])
@handle_exceptions
def get_branch_deletion_summary():
    """获取分支删除汇总统计（JSON格式）"""
    params = get_request_params({
        'repository_id': {'type': int, 'required': False}
    })
    
    rule_service = BranchRuleService()
    report = rule_service.get_branch_deletion_report(params['repository_id'])
    
    return api_response(data=asdict(report))

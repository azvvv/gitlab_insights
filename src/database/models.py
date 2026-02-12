from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Date, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class User(Base):
    """用户表 - 用于系统登录认证"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True, unique=True, index=True)  # 添加唯一索引，避免重复
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime, nullable=True)
    
    def set_password(self, password: str):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典，不包含密码"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f"<User(username='{self.username}', is_admin={self.is_admin})>"

class GitlabApiAccessLog(Base):
    __tablename__ = 'gitlab_api_access_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    access_time = Column(DateTime, nullable=False)
    client_ip = Column(String(45), nullable=False)
    http_method = Column(String(10), nullable=False)
    api_path = Column(Text, nullable=False)
    http_status = Column(Integer, nullable=False)
    response_size = Column(Integer, nullable=True)
    user_agent = Column(Text, nullable=True)
    response_time = Column(Float, nullable=True)
    extra = Column(JSON, nullable=True)

class LogImportStatus(Base):
    __tablename__ = 'log_import_status'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    import_date = Column(Date, nullable=False, unique=True)
    record_count = Column(Integer, nullable=False, default=0)
    import_time = Column(DateTime, nullable=False, default=datetime.now)
    log_file_path = Column(String(500), nullable=True)
    is_complete = Column(Boolean, nullable=False, default=True)

class GitlabRepository(Base):
    __tablename__ = 'gitlab_repository'
    
    id = Column(Integer, primary_key=True)  # GitLab仓库ID
    name = Column(String(255), nullable=False)
    name_with_namespace = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    web_url = Column(String(500), nullable=True)
    ssh_url_to_repo = Column(String(500), nullable=True)
    http_url_to_repo = Column(String(500), nullable=True)
    default_branch = Column(String(100), nullable=True)
    visibility = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    sync_time = Column(DateTime, nullable=False, default=datetime.now)

# 表2：组织及其用户表
class GitlabGroup(Base):
    __tablename__ = 'gitlab_group'
    
    id = Column(Integer, primary_key=True)  # GitLab组ID
    name = Column(String(255), nullable=False)
    path = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    web_url = Column(String(500), nullable=True)
    visibility = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=True)
    sync_time = Column(DateTime, nullable=False, default=datetime.now)

class GitlabGroupMember(Base):
    __tablename__ = 'gitlab_group_member'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('gitlab_group.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    access_level = Column(Integer, nullable=False)
    access_level_name = Column(String(50), nullable=True)
    sync_time = Column(DateTime, nullable=False, default=datetime.now)
    
    group = relationship("GitlabGroup", backref="members")

# 分支规则表（手动维护）- 必须在 GitlabRepositoryBranch 之前定义
class GitlabBranchRule(Base):
    __tablename__ = 'gitlab_branch_rule'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(100), nullable=False, unique=True)  # 规则名称
    branch_pattern = Column(String(255), nullable=False)  # 分支名称匹配模式，支持通配符
    branch_type = Column(String(50), nullable=False)  # 分支类型：master/main, develop, feature, release, hotfix, etc.
    is_deletable = Column(Boolean, nullable=False, default=True)  # 是否可删除
    retention_days = Column(Integer, nullable=True)  # 保留天数，NULL表示永久保留
    description = Column(Text, nullable=True)  # 规则描述
    is_active = Column(Boolean, nullable=False, default=True)  # 规则是否启用
    priority = Column(Integer, nullable=False, default=0)  # 优先级，数字越大优先级越高
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<GitlabBranchRule(name='{self.rule_name}', pattern='{self.branch_pattern}', type='{self.branch_type}')>"

# 表3：仓库分支信息表
class GitlabRepositoryBranch(Base):
    __tablename__ = 'gitlab_repository_branch'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey('gitlab_repository.id'), nullable=False)
    branch_name = Column(String(255), nullable=False)
    commit_id = Column(String(40), nullable=True)
    commit_message = Column(Text, nullable=True)
    commit_author_name = Column(String(255), nullable=True)
    commit_author_email = Column(String(255), nullable=True)
    last_commit_date = Column(DateTime, nullable=True)
    protected = Column(Boolean, nullable=False, default=False)
    
    # 新增字段 - 用于标识分支是否可删除，供用户参考
    is_deletable = Column(Boolean, nullable=True, default=False)  # 是否可删除（根据规则计算）
    matched_rule_id = Column(Integer, ForeignKey('gitlab_branch_rule.id'), nullable=True)  # 匹配的规则ID
    branch_type = Column(String(50), nullable=True)  # 分支类型（根据规则确定）
    retention_deadline = Column(DateTime, nullable=True)  # 保留截止时间
    deletion_reason = Column(Text, nullable=True)  # 建议删除的原因
    
    sync_time = Column(DateTime, nullable=False, default=datetime.now)
    
    repository = relationship("GitlabRepository", backref="branches")
    matched_rule = relationship("GitlabBranchRule", backref="matched_branches")

# 表4：仓库权限信息表
class GitlabRepositoryPermission(Base):
    __tablename__ = 'gitlab_repository_permission'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey('gitlab_repository.id'), nullable=False)
    member_type = Column(String(20), nullable=False)  # 'user' 或 'group'
    member_id = Column(Integer, nullable=False)
    member_name = Column(String(255), nullable=True)
    access_level = Column(Integer, nullable=False)
    access_level_name = Column(String(50), nullable=True)
    sync_time = Column(DateTime, nullable=False, default=datetime.now)
    
    repository = relationship("GitlabRepository", backref="permissions")

# 分支清理历史汇总表 - 添加在现有模型之后
class GitlabBranchCleanupHistory(Base):
    __tablename__ = 'gitlab_branch_cleanup_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基础信息
    report_date = Column(Date, nullable=False)  # 数据生成日期（按天统计）
    generation_time = Column(DateTime, nullable=False, default=datetime.now)  # 具体生成时间
    
    # 分支统计
    total_branches = Column(Integer, nullable=False, default=0)  # 总分支数
    deletable_branches = Column(Integer, nullable=False, default=0)  # 可删除分支数
    protected_branches = Column(Integer, nullable=False, default=0)  # 受保护分支数
    expired_branches = Column(Integer, nullable=False, default=0)  # 已过期分支数
    
    # 按分支类型统计
    feature_branches = Column(Integer, nullable=False, default=0)  # 功能分支数
    bugfix_branches = Column(Integer, nullable=False, default=0)  # 修复分支数
    hotfix_branches = Column(Integer, nullable=False, default=0)  # 热修复分支数
    release_branches = Column(Integer, nullable=False, default=0)  # 发布分支数
    archive_branches = Column(Integer, nullable=False, default=0)  # 归档分支数
    main_branches = Column(Integer, nullable=False, default=0)  # 主分支数
    other_branches = Column(Integer, nullable=False, default=0)  # 其他分支数
    
    # 按可删除类型统计
    deletable_feature = Column(Integer, nullable=False, default=0)  # 可删除功能分支
    deletable_bugfix = Column(Integer, nullable=False, default=0)  # 可删除修复分支
    deletable_archive = Column(Integer, nullable=False, default=0)  # 可删除归档分支
    deletable_other = Column(Integer, nullable=False, default=0)  # 可删除其他分支
    
    # 仓库维度统计
    total_repositories = Column(Integer, nullable=False, default=0)  # 涉及仓库总数
    repositories_with_cleanup = Column(Integer, nullable=False, default=0)  # 有可清理分支的仓库数
    
    # 时间维度统计
    branches_over_30_days = Column(Integer, nullable=False, default=0)  # 超过30天未更新的分支
    branches_over_60_days = Column(Integer, nullable=False, default=0)  # 超过60天未更新的分支
    branches_over_90_days = Column(Integer, nullable=False, default=0)  # 超过90天未更新的分支
    branches_over_180_days = Column(Integer, nullable=False, default=0)  # 超过180天未更新的分支
    
    # 规则匹配统计
    matched_rules_count = Column(Integer, nullable=False, default=0)  # 匹配到规则的分支数
    unmatched_branches = Column(Integer, nullable=False, default=0)  # 未匹配规则的分支数
    
    # 存储空间估算（可选）
    estimated_storage_mb = Column(Float, nullable=True)  # 估算的存储空间(MB)
    
    # 数据源信息
    sync_version = Column(String(50), nullable=True)  # 同步程序版本
    data_source = Column(String(100), nullable=True, default='GitLab API')  # 数据源
    
    # 索引和约束
    __table_args__ = (
        # 确保每天只有一条记录
        # Index('idx_cleanup_history_date', 'report_date', unique=True),
    )
    
    def __repr__(self):
        return f"<GitlabBranchCleanupHistory(date={self.report_date}, total={self.total_branches}, deletable={self.deletable_branches})>"
# Jenkins Job 记录表
class JenkinsJobRecord(Base):
    __tablename__ = 'jenkins_job_record'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # GitLab相关
    gitlab_source_branch = Column(String(255), nullable=True)
    gitlab_target_branch = Column(String(255), nullable=True)
    gitlab_user_name = Column(String(255), nullable=True)
    gitlab_user_email = Column(String(255), nullable=True)
    gitlab_action_type = Column(String(100), nullable=True)
    gitlab_source_repo_homepage = Column(String(500), nullable=True)
    gitlab_source_repo_name = Column(String(255), nullable=True)
    gitlab_source_namespace = Column(String(255), nullable=True)
    gitlab_source_repo_url = Column(String(500), nullable=True)
    gitlab_source_repo_ssh_url = Column(String(500), nullable=True)
    gitlab_merge_request_title = Column(Text, nullable=True)
    gitlab_merge_request_description = Column(Text, nullable=True)
    gitlab_merge_request_id = Column(String(100), nullable=True)
    gitlab_merge_request_iid = Column(String(100), nullable=True)
    gitlab_merge_request_state = Column(String(50), nullable=True)
    gitlab_merged_by_user = Column(String(255), nullable=True)
    gitlab_merge_request_assignee = Column(String(255), nullable=True)
    gitlab_merge_request_last_commit = Column(String(100), nullable=True)
    gitlab_merge_request_target_project_id = Column(String(100), nullable=True)
    gitlab_target_repo_name = Column(String(255), nullable=True)
    gitlab_commit_message = Column(Text, nullable=True)
    gitlab_commit_hash = Column(String(100), nullable=True)

    # Jenkins相关
    job_display_url = Column(String(500), nullable=True)
    branch_name = Column(String(255), nullable=True)
    build_number = Column(String(50), nullable=True)
    build_id = Column(String(100), nullable=True)
    build_display_name = Column(String(255), nullable=True)
    job_name = Column(String(255), nullable=True)
    job_base_name = Column(String(255), nullable=True)
    jenkins_url = Column(String(500), nullable=True)
    build_url = Column(String(500), nullable=True)
    job_url = Column(String(500), nullable=True)

    # currentBuild相关
    build_causes = Column(Text, nullable=True)
    build_result = Column(String(50), nullable=True)
    build_current_result = Column(String(50), nullable=True)
    build_start_time_in_millis = Column(String(50), nullable=True)
    build_duration_string = Column(String(100), nullable=True)
    build_duration = Column(String(50), nullable=True)

    # 记录时间
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<JenkinsJobRecord(id={self.id}, job_name={self.job_name}, build_number={self.build_number})>"

class GitlabTagRelation(Base):
    __tablename__ = 'gitlab_tag_relation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    apk_tag = Column(String(255), nullable=True, unique=True)  # APK最终产物的tag
    nena_tag = Column(String(255), nullable=True)  # nena仓库tag
    ocserver_tag = Column(String(255), nullable=True)  # ocserver仓库tag
    clientcpp_tag = Column(String(255), nullable=True)  # clientcpp仓库tag
    onecloudserver_tag = Column(String(255), nullable=True)  # onecloudserver仓库tag
    onecloudclient_tag = Column(String(255), nullable=True)  # onecloudclient仓库tag
    otaweb_tag = Column(String(255), nullable=True)  # otaweb仓库tag
    nmasdkapi_tag = Column(String(255), nullable=True)  # nmasdkapi仓库tag
    nmasdkbl_tag = Column(String(255), nullable=True)  # nmasdkbl仓库tag
    nmasdkhmi_tag = Column(String(255), nullable=True)  # nmasdkhmi仓库tag
    user = Column(String(255), nullable=True)  # 记录操作人
    jenkins_job = Column(String(500), nullable=True)  # Jenkins Job URL，对应JenkinsJobRecord.build_url
    description = Column(Text, nullable=True)  # 备注或描述
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    sync_time = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<GitlabTagRelation(apk_tag={self.apk_tag})>"


class GitlabSubmoduleUpdateRecord(Base):
    """记录一次对父仓库中所有 submodule 指针更新的操作结果（按分支/批次）。"""
    __tablename__ = 'gitlab_submodule_update_record'

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_project_id = Column(Integer, ForeignKey('gitlab_repository.id'), nullable=False)
    target_branch = Column(String(255), nullable=True)  # 新建的分支名或推送目标
    status = Column(String(50), nullable=False, default='pending')  # pending/success/partial/failure
    details = Column(JSON, nullable=True)  # 存放每个子模块的结果列表
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    parent = relationship('GitlabRepository', backref='submodule_update_records')


class GitlabBranchCreateRecord(Base):
    """记录由脚本/服务发起的创建分支操作及其来源 commit 信息、结果状态。"""
    __tablename__ = 'gitlab_branch_create_record'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('gitlab_repository.id'), nullable=False)
    branch_name = Column(String(255), nullable=False, index=True)  # 添加索引便于查询
    source_ref = Column(String(255), nullable=True)  # the ref used to create from (branch/tag/name)
    source_commit = Column(String(100), nullable=True)  # resolved commit id (sha)
    status = Column(String(500), nullable=False, default='pending')  # pending/created/failed/already_exists
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)  # 添加索引便于时间查询
    created_by = Column(String(100), nullable=True)  # 记录操作人
    jira_ticket = Column(String(100), nullable=True, index=True)  # 关联的Jira工单号，记录创建分支的原因

    project = relationship('GitlabRepository', backref='branch_create_records')

# 监控数据时序表 - 用于存储各种应用的监控指标数据
class MonitoringMetric(Base):
    __tablename__ = 'monitoring_metric'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 时间维度
    metric_date = Column(Date, nullable=False, index=True)  # 指标日期（按天统计）
    metric_timestamp = Column(DateTime, nullable=False, default=datetime.now)  # 具体采集时间
    
    # 应用标识
    application = Column(String(100), nullable=False, index=True)  # 应用名称，如：jira, gitlab, jenkins等
    metric_type = Column(String(100), nullable=False, index=True)  # 指标类型，如：user_count, license_count等
    
    # 指标数据
    metric_value = Column(Float, nullable=True)  # 数值型指标值
    metric_value_int = Column(Integer, nullable=True)  # 整数型指标值（用于用户数等）
    metric_value_text = Column(Text, nullable=True)  # 文本型指标值
    metric_unit = Column(String(50), nullable=True)  # 指标单位，如：count, MB, GB等
    
    # 扩展信息
    metric_metadata = Column(JSON, nullable=True)  # 扩展元数据，存储JSON格式的额外信息
    status = Column(String(50), nullable=True)  # 采集状态：success, failed, partial等
    error_message = Column(Text, nullable=True)  # 错误信息（如果采集失败）
    
    # 数据源信息
    data_source = Column(String(200), nullable=True)  # 数据源URL或标识
    collection_method = Column(String(100), nullable=True)  # 采集方式：api, manual, scheduled等
    
    # 创建时间
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # 复合索引
    __table_args__ = (
        # 确保每个应用每天每种指标类型只有一条记录
        # Index('idx_monitoring_unique', 'metric_date', 'application', 'metric_type', unique=True),
        # 查询性能优化索引
        # Index('idx_monitoring_app_type_date', 'application', 'metric_type', 'metric_date'),
    )
    
    def __repr__(self):
        return f"<MonitoringMetric(date={self.metric_date}, app={self.application}, type={self.metric_type}, value={self.metric_value_int or self.metric_value})>"

class HomeLink(Base):
    """首页链接配置表"""
    __tablename__ = 'home_links'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)  # 分类：doc_links, platform_links
    group_name = Column(String(50), nullable=False, index=True)  # 分组：devops, jira, ai, monitoring等
    title = Column(String(100), nullable=False)  # 链接标题
    description = Column(Text, nullable=True)  # 链接描述
    url = Column(String(500), nullable=False)  # 链接地址
    icon = Column(String(100), nullable=True)  # 图标名称
    color = Column(String(500), nullable=True)  # 颜色（CSS渐变色）
    ip = Column(String(50), nullable=True)  # 平台IP地址
    port = Column(String(10), nullable=True)  # 平台端口
    sort_order = Column(Integer, nullable=False, default=0)  # 排序顺序
    is_active = Column(Boolean, nullable=False, default=True, index=True)  # 是否启用
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<HomeLink(category='{self.category}', group='{self.group_name}', title='{self.title}')>"


class GitlabBranchSummary(Base):
    """GitLab 分支汇总统计表 - 用于快速查询和展示"""
    __tablename__ = 'gitlab_branch_summary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 仓库信息
    repository_id = Column(Integer, ForeignKey('gitlab_repository.id'), nullable=False, index=True)
    repository_name = Column(String(255), nullable=True)  # 冗余字段，加快查询
    
    # 分支类型统计
    total_branches = Column(Integer, nullable=False, default=0)  # 总分支数
    protected_branches = Column(Integer, nullable=False, default=0)  # 受保护分支数
    deletable_branches = Column(Integer, nullable=False, default=0)  # 可删除分支数
    
    # 按分支类型分组统计（固定类型，便于查询和排序）
    feature_branches = Column(Integer, nullable=False, default=0)  # feature 分支数
    develop_branches = Column(Integer, nullable=False, default=0)  # develop 分支数
    release_branches = Column(Integer, nullable=False, default=0)  # release 分支数
    hotfix_branches = Column(Integer, nullable=False, default=0)  # hotfix 分支数
    main_branches = Column(Integer, nullable=False, default=0)  # main/master 分支数
    stabilization_branches = Column(Integer, nullable=False, default=0)  # stabilization 分支数
    other_branches = Column(Integer, nullable=False, default=0)  # 未分类或其他分支数
    
    # 按活跃度统计（基于最后提交时间）
    active_30days = Column(Integer, nullable=False, default=0)  # 30天内活跃
    active_90days = Column(Integer, nullable=False, default=0)  # 90天内活跃
    inactive_180days = Column(Integer, nullable=False, default=0)  # 180天以上未活跃
    inactive_365days = Column(Integer, nullable=False, default=0)  # 365天以上未活跃
    
    # 最新分支信息
    latest_branch_name = Column(String(255), nullable=True)  # 最新创建的分支
    latest_branch_date = Column(DateTime, nullable=True)  # 最新分支创建时间
    oldest_branch_name = Column(String(255), nullable=True)  # 最旧的分支
    oldest_branch_date = Column(DateTime, nullable=True)  # 最旧分支创建时间
    
    # 默认分支信息
    default_branch = Column(String(100), nullable=True)  # 默认分支名
    default_branch_commit = Column(String(40), nullable=True)  # 默认分支最新提交
    default_branch_last_commit_date = Column(DateTime, nullable=True)  # 默认分支最后提交时间
    
    # 统计元数据
    last_sync_time = Column(DateTime, nullable=False, default=datetime.now, index=True)  # 最后同步时间
    data_version = Column(Integer, nullable=False, default=1)  # 数据版本号
    
    # 扩展信息（JSON格式，存储额外统计数据）
    extra_stats = Column(JSON, nullable=True)  # 如：按作者统计、按规则匹配统计等
    
    # 关系
    repository = relationship('GitlabRepository', backref='branch_summary')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'repository_id': self.repository_id,
            'repository_name': self.repository_name,
            'total_branches': self.total_branches,
            'protected_branches': self.protected_branches,
            'deletable_branches': self.deletable_branches,
            'feature_branches': self.feature_branches,
            'develop_branches': self.develop_branches,
            'release_branches': self.release_branches,
            'hotfix_branches': self.hotfix_branches,
            'main_branches': self.main_branches,
            'stabilization_branches': self.stabilization_branches,
            'other_branches': self.other_branches,
            'active_30days': self.active_30days,
            'active_90days': self.active_90days,
            'inactive_180days': self.inactive_180days,
            'inactive_365days': self.inactive_365days,
            'latest_branch_name': self.latest_branch_name,
            'latest_branch_date': self.latest_branch_date.isoformat() if self.latest_branch_date else None,
            'oldest_branch_name': self.oldest_branch_name,
            'oldest_branch_date': self.oldest_branch_date.isoformat() if self.oldest_branch_date else None,
            'default_branch': self.default_branch,
            'default_branch_commit': self.default_branch_commit,
            'default_branch_last_commit_date': self.default_branch_last_commit_date.isoformat() if self.default_branch_last_commit_date else None,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'data_version': self.data_version,
            'extra_stats': self.extra_stats
        }
    
    def __repr__(self):
        return f"<GitlabBranchSummary(repo_id={self.repository_id}, total={self.total_branches})>"

def create_tables(engine):
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)
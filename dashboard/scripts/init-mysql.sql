-- LiveKit Dashboard 数据库初始化脚本
-- MySQL 8.0+

-- 创建数据库
CREATE DATABASE IF NOT EXISTS livekit_dashboard 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE livekit_dashboard;

-- 创建用户（如果不存在）
CREATE USER IF NOT EXISTS 'livekit'@'%' IDENTIFIED BY 'livekit_password';

-- 授权
GRANT ALL PRIVILEGES ON livekit_dashboard.* TO 'livekit'@'%';
FLUSH PRIVILEGES;

-- Agent配置表
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(64) PRIMARY KEY COMMENT 'Agent唯一ID',
    name VARCHAR(100) NOT NULL COMMENT 'Agent名称',
    description TEXT COMMENT 'Agent描述',
    agent_type ENUM('voice', 'video', 'text') DEFAULT 'voice' COMMENT 'Agent类型',
    
    -- LiveKit配置
    livekit_url VARCHAR(512) COMMENT 'LiveKit服务器URL',
    livekit_api_key VARCHAR(128) COMMENT 'LiveKit API密钥',
    livekit_api_secret VARCHAR(256) COMMENT 'LiveKit API密文',
    
    -- 模型配置（JSON）
    stt_config JSON COMMENT 'STT模型配置',
    llm_config JSON COMMENT 'LLM模型配置',
    tts_config JSON COMMENT 'TTS模型配置',
    vad_config JSON COMMENT 'VAD模型配置',
    
    -- 高级配置
    instructions TEXT COMMENT 'Agent指令',
    max_tool_steps INT DEFAULT 5 COMMENT '最大工具调用步数',
    allow_interruptions BOOLEAN DEFAULT TRUE COMMENT '是否允许打断',
    
    -- 运行状态
    status ENUM('idle', 'running', 'error', 'starting', 'stopping') DEFAULT 'idle' COMMENT '运行状态',
    pid INT COMMENT '进程ID',
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(64) DEFAULT 'user' COMMENT '创建者',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent配置表';

-- 会话记录表
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(64) PRIMARY KEY COMMENT '会话ID',
    agent_id VARCHAR(64) NOT NULL COMMENT 'Agent ID',
    room_name VARCHAR(128) COMMENT '房间名称',
    participant_identity VARCHAR(128) COMMENT '参与者身份',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    ended_at TIMESTAMP NULL COMMENT '结束时间',
    status ENUM('active', 'completed', 'error') DEFAULT 'active' COMMENT '会话状态',
    
    -- 会话统计
    user_messages INT DEFAULT 0 COMMENT '用户消息数',
    agent_messages INT DEFAULT 0 COMMENT 'Agent消息数',
    total_duration FLOAT DEFAULT 0 COMMENT '总时长（秒）',
    
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    INDEX idx_agent_id (agent_id),
    INDEX idx_started_at (started_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话记录表';

-- 日志表
CREATE TABLE IF NOT EXISTS logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    agent_id VARCHAR(64) COMMENT 'Agent ID',
    session_id VARCHAR(64) COMMENT '会话ID',
    timestamp TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3) COMMENT '日志时间（毫秒精度）',
    level ENUM('TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL') NOT NULL COMMENT '日志级别',
    message TEXT NOT NULL COMMENT '日志内容',
    metadata JSON COMMENT '额外元数据',
    
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
    INDEX idx_agent_id (agent_id),
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_level (level),
    INDEX idx_logs_composite (agent_id, level, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='日志表';

-- 性能指标表
CREATE TABLE IF NOT EXISTS metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '指标ID',
    agent_id VARCHAR(64) NOT NULL COMMENT 'Agent ID',
    timestamp TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3) COMMENT '采集时间',
    cpu_usage FLOAT COMMENT 'CPU使用率（%）',
    memory_usage FLOAT COMMENT '内存使用（MB）',
    active_sessions INT DEFAULT 0 COMMENT '活跃会话数',
    messages_per_minute INT DEFAULT 0 COMMENT '每分钟消息数',
    avg_response_time FLOAT COMMENT '平均响应时间（秒）',
    
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    INDEX idx_agent_id (agent_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='性能指标表';

-- API密钥表
CREATE TABLE IF NOT EXISTS api_keys (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '密钥ID',
    service_name VARCHAR(64) NOT NULL COMMENT '服务名称',
    api_key VARCHAR(512) NOT NULL COMMENT 'API密钥（加密存储）',
    api_endpoint VARCHAR(512) COMMENT 'API端点',
    is_valid BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    last_tested_at TIMESTAMP NULL COMMENT '最后测试时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_service_name (service_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API密钥表';

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    config_key VARCHAR(64) PRIMARY KEY COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(256) COMMENT '配置说明',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 初始化系统配置数据
INSERT INTO system_config (config_key, config_value, description) VALUES
    ('log_retention_days', '30', '日志保留天数'),
    ('max_sessions_per_agent', '100', '每个Agent最大并发会话数'),
    ('default_log_level', 'INFO', '默认日志级别'),
    ('enable_metrics', 'true', '是否启用性能指标采集'),
    ('metrics_interval', '60', '性能指标采集间隔（秒）'),
    ('db_version', '1.0', '数据库版本')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 创建存储过程：清理旧日志
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS cleanup_old_logs(IN days_to_keep INT)
BEGIN
    DELETE FROM logs 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    SELECT ROW_COUNT() AS deleted_rows;
END //
DELIMITER ;

-- 创建存储过程：创建日志分区
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS create_log_partition(IN days_offset INT)
BEGIN
    DECLARE partition_name VARCHAR(20);
    DECLARE partition_value INT;
    
    SET partition_name = CONCAT('p_', DATE_FORMAT(DATE_ADD(CURDATE(), INTERVAL days_offset DAY), '%Y%m%d'));
    SET partition_value = UNIX_TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL days_offset + 1 DAY));
    
    SET @sql = CONCAT('ALTER TABLE logs REORGANIZE PARTITION p_default INTO (
        PARTITION ', partition_name, ' VALUES LESS THAN (', partition_value, '),
        PARTITION p_default VALUES LESS THAN (MAXVALUE)
    )');
    
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //
DELIMITER ;

-- 创建视图：最近1小时的日志
CREATE OR REPLACE VIEW recent_logs AS
SELECT 
    l.id,
    l.agent_id,
    a.name AS agent_name,
    l.session_id,
    l.timestamp,
    l.level,
    l.message,
    l.metadata
FROM logs l
LEFT JOIN agents a ON l.agent_id = a.id
WHERE l.timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
ORDER BY l.timestamp DESC;

-- 完成
SELECT 'Database initialization completed successfully!' AS message;
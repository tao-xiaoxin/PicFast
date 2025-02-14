/*
图片表
Created by: tao-xiaoxin
Created time: 2025-02-14 07:18:52
*/

CREATE TABLE `images` (
    `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '图片ID',
    `key` varchar(32) NOT NULL COMMENT '图片唯一标识(MD5)',
    `original_name` varchar(255) DEFAULT NULL COMMENT '原始文件名',
    `extension` varchar(10) NOT NULL COMMENT '文件后缀',
    `size` bigint NOT NULL COMMENT '文件大小(字节)',
    `mime_type` varchar(128) NOT NULL COMMENT '文件MIME类型',
    `storage_path` varchar(255) NOT NULL COMMENT '存储路径',
    `view_count` bigint NOT NULL DEFAULT '0' COMMENT '浏览次数',
    `status` tinyint(1) NOT NULL DEFAULT '1' COMMENT '状态(0-禁用,1-启用)',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_key` (`key`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_view_count` (`view_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图片表';
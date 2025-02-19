/*
图片表
Created by: tao-xiaoxin
Created time: 2025-02-14 08:10:43
*/
-- 图片记录存储表
CREATE TABLE `pf_images`
(
    `id`            bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '图片ID',
    `key`           varchar(32)     NOT NULL COMMENT '图片唯一标识(MD5)',
    `original_name` varchar(255)             DEFAULT NULL COMMENT '原始文件名',
    `size`          decimal(10, 2)  NOT NULL COMMENT '文件大小(MB)', -- 使用 decimal(10,2) 保证精确度
    `mime_type`     varchar(128)    NOT NULL COMMENT '文件MIME类型',
    `storage_path`  varchar(255)    NOT NULL COMMENT '存储路径',
    `view_count`    bigint          NOT NULL DEFAULT '0' COMMENT '浏览次数',
    `created_at`    datetime        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`    datetime        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_key` (`key`),
    KEY `idx_created_at` (`created_at`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='图片表';

-- 创建访问密钥表
CREATE TABLE fp_access_keys
(
    id           INTEGER PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    name         VARCHAR(50)  NOT NULL COMMENT '密钥名称',
    access_key   VARCHAR(100) NOT NULL COMMENT '访问密钥',
    secret_key   VARCHAR(100) NOT NULL COMMENT '密钥',
    is_enabled   BOOLEAN      NOT NULL DEFAULT TRUE COMMENT '是否启用',
    description  VARCHAR(200) NULL COMMENT '描述',
    expires_at   DATETIME     NULL COMMENT '过期时间',
    last_used_at DATETIME     NULL COMMENT '最后使用时间',
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE INDEX idx_access_key (access_key)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
    COMMENT ='访问密钥表';
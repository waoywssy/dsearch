/*
Navicat MySQL Data Transfer

Source Server         : VM7Desk
Source Server Version : 50723
Source Host           : 192.168.0.21:3306
Source Database       : search

Target Server Type    : MYSQL
Target Server Version : 50723
File Encoding         : 65001

Date: 2018-08-08 10:05:37
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for `histories`
-- ----------------------------
DROP TABLE IF EXISTS `histories`;
CREATE TABLE `histories` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `firstId` bigint(20) NOT NULL,
  `secondId` bigint(20) NOT NULL,
  `count` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_firstId` (`firstId`) USING BTREE,
  KEY `idx_secondId` (`secondId`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- ----------------------------
-- Records of histories
-- ----------------------------

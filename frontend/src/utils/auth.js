/**
 * 权限工具
 */

/**
 * 角色ID枚举
 */
export const RoleEnum = {
  SUPER_ADMIN: 1,
  AUDITOR: 2,
  USER: 3
}

/**
 * 角色名称映射
 */
export const RoleNameMap = {
  1: '超级管理员',
  2: '审核员',
  3: '普通用户'
}

/**
 * 判断是否是超级管理员
 */
export function isSuperAdmin(roleId) {
  return roleId === RoleEnum.SUPER_ADMIN
}

/**
 * 判断是否是审核员
 */
export function isAuditor(roleId) {
  return roleId === RoleEnum.AUDITOR
}

/**
 * 判断是否是普通用户
 */
export function isUser(roleId) {
  return roleId === RoleEnum.USER
}

/**
 * 判断是否有访问权限
 */
export function hasPermission(roleId, allowedRoles) {
  return allowedRoles.includes(roleId)
}

/**
 * 获取角色名称
 */
export function getRoleName(roleId) {
  return RoleNameMap[roleId] || '未知角色'
}
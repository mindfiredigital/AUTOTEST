export function hasRole(userRole: string, allowedRoles: string[]) {
  return allowedRoles.includes(userRole)
}

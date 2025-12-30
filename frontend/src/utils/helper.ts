// export function hasRole(userRole: string, allowedRoles: string[]) {
//   return allowedRoles.includes(userRole)
// }

import { type Role } from './constants'

export const hasRole = (userRole: string | string[], allowedRoles: Role[]): boolean => {
  if (Array.isArray(userRole)) {
    return userRole.some((role) => allowedRoles.includes(role as Role))
  }
  return allowedRoles.includes(userRole as Role)
}

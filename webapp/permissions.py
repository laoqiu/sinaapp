#! /usr/bin/env python
#coding=utf-8
from flaskext.principal import RoleNeed, Permission

admin_permission = Permission(RoleNeed('admin'))
moderator_permission = Permission(RoleNeed('moderator'))
auth_permission = Permission(RoleNeed('authenticated'))

# this is assigned when you want to block a permission to all
# never assign this role to anyone !
null_permission = Permission(RoleNeed('null'))

import request from '@/config/axios'

export const getMenuListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/system/menus', params })
}

export const delMenuListApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/system/menus', data })
}

export const addMenuListApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/system/menus', data })
}

export const putMenuListApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/system/menus/${data.id}`, data })
}

export const getMenuTreeOptionsApi = (): Promise<IResponse> => {
  return request.get({ url: '/vadmin/system/menus/tree/options' })
}

export const getMenuRoleTreeOptionsApi = (): Promise<IResponse> => {
  return request.get({ url: '/vadmin/system/menus/role/tree/options' })
}


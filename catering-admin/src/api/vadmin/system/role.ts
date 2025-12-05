import request from '@/config/axios'

export const getRoleListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/system/roles', params })
}

export const addRoleListApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/system/roles', data })
}

export const delRoleListApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/system/roles', data })
}

export const putRoleListApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/system/roles/${data.id}`, data })
}

export const getRoleApi = (dataId: number): Promise<IResponse> => {
  return request.get({ url: `/vadmin/system/roles/${dataId}` })
}

export const getRoleOptionsApi = (): Promise<IResponse> => {
  return request.get({ url: `/vadmin/system/roles/options` })
}


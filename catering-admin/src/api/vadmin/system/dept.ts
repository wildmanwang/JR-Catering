import request from '@/config/axios'

export const getDeptListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/system/depts', params })
}

export const delDeptListApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/system/depts', data })
}

export const addDeptListApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/system/depts', data })
}

export const putDeptListApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/system/depts/${data.id}`, data })
}

export const getDeptTreeOptionsApi = (): Promise<IResponse> => {
  return request.get({ url: '/vadmin/system/dept/tree/options' })
}

export const getDeptUserTreeOptionsApi = (): Promise<IResponse> => {
  return request.get({ url: '/vadmin/system/dept/user/tree/options' })
}


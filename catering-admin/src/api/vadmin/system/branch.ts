import request from '@/config/axios'
 
export const getBranchListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/system/branches', params })
}

export const addBranchListApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/system/branches', data })
}
    
export const delBranchListApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/system/branches', data })
}

export const putBranchListApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/system/branches/${data.id}`, data })
}

export const getBranchApi = (dataId: number): Promise<IResponse> => {
  return request.get({ url: `/vadmin/system/branches/${dataId}` })
}

import request from '@/config/axios'
 
export const getBranchListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/system/branch', params })
}

export const addBranchListApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/system/branch', data })
}
    
export const delBranchListApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/system/branch', data })
}

export const putBranchListApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/system/branch/${data.id}`, data })
}

export const getBranchApi = (dataId: number): Promise<IResponse> => {
  return request.get({ url: `/vadmin/system/branch/${dataId}` })
}

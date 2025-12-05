import request from '@/config/axios'

export const getKitchenListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/product/kitchen', params })
}

export const addKitchenListApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/product/kitchen', data })
}

export const delKitchenListApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/product/kitchen', data })
}

export const putKitchenListApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/product/kitchen/${data.id}`, data })
}

export const getKitchenApi = (dataId: number): Promise<IResponse> => {
  return request.get({ url: `/vadmin/product/kitchen/${dataId}` })
}

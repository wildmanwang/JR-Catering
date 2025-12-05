import request from '@/config/axios'


export const getDishStatusOptionsApi = (): Promise<IResponse> => {
  return request.get({ url: '/vadmin/product/dishstatusoptions' })
}

export const getDishListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/product/dish', params })
}

export const addDishListApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/product/dish', data })
}

export const delDishListApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/product/dish', data })
}

export const putDishListApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/product/dish/${data.id}`, data })
}

export const getDishApi = (dataId: number): Promise<IResponse> => {
  return request.get({ url: `/vadmin/product/dish/${dataId}` })
}

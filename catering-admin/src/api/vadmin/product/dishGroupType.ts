import request from '@/config/axios'


export const getDishGroupTypeStatusOptionsApi = (): Promise<IResponse> => {
  return request.get({ url: '/vadmin/product/dishgrouptypestatusoptions' })
}

export const getDishGroupTypeListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/product/dishgrouptype', params })
}

export const addDishGroupTypeApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/product/dishgrouptype', data })
}

export const delDishGroupTypeApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/product/dishgrouptype', data })
}

export const putDishGroupTypeApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/product/dishgrouptype/${data.id}`, data })
}

export const getDishGroupTypeApi = (dataId: number): Promise<IResponse> => {
  return request.get({ url: `/vadmin/product/dishgrouptype/${dataId}` })
}

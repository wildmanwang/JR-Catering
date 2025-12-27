import request from '@/config/axios'


export const getDishGroupStypeOptionsApi = (): Promise<IResponse> => {
  return request.get({ url: '/vadmin/product/dishgroupstypeoptions' })
}

export const getDishGroupListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/product/dishgroup', params })
}

export const addDishGroupApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/product/dishgroup', data })
}

export const delDishGroupApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/product/dishgroup', data })
}

export const putDishGroupApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/product/dishgroup/${data.id}`, data })
}

export const getDishGroupApi = (dataId: number): Promise<IResponse> => {
  return request.get({ url: `/vadmin/product/dishgroup/${dataId}` })
}

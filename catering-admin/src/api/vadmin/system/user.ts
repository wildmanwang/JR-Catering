import request from '@/config/axios'

export const getUserListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/system/users', params })
}

export const addUserListApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/system/users', data })
}

export const delUserListApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/system/users', data })
}

export const putUserListApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/system/users/${data.id}`, data })
}

export const getUserApi = (dataId: number): Promise<IResponse> => {
  return request.get({ url: `/vadmin/system/users/${dataId}` })
}

export const postCurrentUserResetPassword = (data: any): Promise<IResponse> => {
  return request.post({ url: `/vadmin/system/user/current/reset/password`, data })
}

export const postCurrentUserUpdateInfo = (data: any): Promise<IResponse> => {
  return request.post({ url: `/vadmin/system/user/current/update/info`, data })
}

export const getCurrentAdminUserInfo = (): Promise<IResponse> => {
  return request.get({ url: `/vadmin/system/user/admin/current/info` })
}

export const postExportUserQueryListApi = (params: any, data: any): Promise<IResponse> => {
  return request.post({ url: `/vadmin/system/user/export/query/list/to/excel`, params, data })
}

export const getImportTemplateApi = (): Promise<IResponse> => {
  return request.get({ url: `/vadmin/system/user/download/import/template` })
}

export const postImportUserApi = (data: any): Promise<IResponse> => {
  return request.post({
    url: `/vadmin/system/import/users`,
    headersType: 'multipart/form-data',
    data
  })
}

export const postUsersInitPasswordSendSMSApi = (data: any): Promise<IResponse> => {
  return request.post({ url: `/vadmin/system/users/init/password/send/sms`, data })
}

export const postUsersInitPasswordSendEmailApi = (data: any): Promise<IResponse> => {
  return request.post({ url: `/vadmin/system/users/init/password/send/email`, data })
}


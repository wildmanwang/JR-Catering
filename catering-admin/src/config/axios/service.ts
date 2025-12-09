import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { useAuthStoreWithOut } from '@/store/modules/auth'
import qs from 'qs'
import { config } from './config'
import { ElMessage } from 'element-plus'
import request from '@/config/axios'

const { result_code, unauthorized_code, request_timeout } = config

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: '/api', // api 的 base_url
  timeout: request_timeout, // 请求超时时间
  headers: {} // 请求头信息
})

// request拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStoreWithOut()
    const token = authStore.getToken
    if (token !== '') {
      ;(config.headers as any)[authStore.getTokenKey ?? 'Authorization'] = token // 让每个请求携带自定义token 请根据实际情况自行修改
    }
    if (
      config.method === 'post' &&
      (config.headers as any)['Content-Type'] === 'application/x-www-form-urlencoded'
    ) {
      config.data = qs.stringify(config.data)
    }
    // post put 参数处理
    if (
      (config.method === 'post' || config.method === 'put') &&
      (config.headers as any)['Content-Type'] === 'application/json'
    ) {
      for (const key in config.data) {
        // 参数处理
        if (config.data[key] === '') {
          config.data[key] = null
        }
      }
    }
    // get参数编码
    if (config.method === 'get' && config.params) {
      let url = config.url as string
      url += '?'
      const keys = Object.keys(config.params)
      for (const key of keys) {
        if (
          // 禁止提交的get参数类型
          config.params[key] !== void 0 &&
          config.params[key] !== null &&
          config.params[key] !== ''
        ) {
          url += `${key}=${encodeURIComponent(config.params[key])}&`
        }
      }
      url = url.substring(0, url.length - 1)
      config.params = {}
      config.url = url
    }
    return config
  },
  (error: AxiosError) => {
    // Do something with request error
    console.log('请求报错', error) // for debug
    Promise.reject(error)
  }
)

// response 拦截器
service.interceptors.response.use(
  (response: AxiosResponse<any>) => {
    // 这个状态码是和后端约定好的
    const code = response.data.code || unauthorized_code
    const message = response.data.message || '后端接口无返回内容'
    const refresh = response.headers['if-refresh']

    if (response.config.responseType === 'blob') {
      // 如果是文件流，直接过
      return response
    } else if (code === result_code) {
      if (refresh === '1') {
        // 因token快过期，刷新token
        refreshToken().then((res) => {
          const authStore = useAuthStoreWithOut()
          authStore.setToken(`${res.data.token_type} ${res.data.access_token}`)
          authStore.setRefreshToken(res.data.refresh_token)
        })
      }
      return response.data
    } else if (code === unauthorized_code) {
      // Token 无效或过期，尝试刷新 Token
      refreshToken().then((res) => {
        const authStore = useAuthStoreWithOut()
        authStore.setToken(`${res.data.token_type} ${res.data.access_token}`)
        authStore.setRefreshToken(res.data.refresh_token)
        ElMessage.error('操作失败，请重试')
      })
      // 返回 rejected promise，让调用方能够捕获错误
      return Promise.reject(new Error(message))
    } else {
      // 业务错误：显示错误消息，并返回 rejected promise 让调用方能够捕获并处理
      ElMessage.error(message)
      return Promise.reject(new Error(message))
    }
  },
  (error: AxiosError) => {
    console.log('err', error)
    let { message } = error
    const authStore = useAuthStoreWithOut()
    const status = error.response?.status
    
    /**
     * 从响应数据中提取错误信息
     * 优先使用后端返回的详细错误消息，支持多种可能的字段名
     */
    const responseData = error.response?.data
    const responseMessage = 
      responseData?.message || 
      responseData?.msg || 
      responseData?.error || 
      responseData?.detail ||
      (typeof responseData === 'string' ? responseData : null)
    
    /**
     * 根据 HTTP 状态码设置错误消息
     * 优先使用后端返回的详细错误信息，如果没有则使用默认消息
     */
    switch (status) {
      case 400:
        message = responseMessage || '请求错误'
        break
      case 401:
        // 认证失败：账号已冻结、账号已过期、手机号码错误、刷新token无效等
        authStore.logout()
        message = responseMessage || '认证已失效，请重新登录'
        break
      case 403:
        // 权限不足：无系统权限访问等问题
        authStore.logout()
        message = responseMessage || '无权限访问，请联系管理员'
        break
      case 404:
        message = responseMessage || `请求地址出错: ${error.response?.config.url}`
        break
      case 408:
        message = responseMessage || '请求超时'
        break
      case 500:
        // 服务器内部错误：优先显示后端返回的详细错误信息
        message = responseMessage || '服务器内部错误'
        break
      case 501:
        message = responseMessage || '服务未实现'
        break
      case 502:
        message = responseMessage || '网关错误'
        break
      case 503:
        message = responseMessage || '服务不可用'
        break
      case 504:
        message = responseMessage || '网关超时'
        break
      case 505:
        message = responseMessage || 'HTTP版本不受支持'
        break
      default:
        // 其他状态码：如果有响应消息则使用，否则保持原始错误消息
        if (responseMessage) {
          message = responseMessage
        }
        break
    }
    
    // 显示错误提示
    ElMessage.error(message)
    
    // 返回包含详细错误信息的 Error 对象，让调用方能够捕获并处理
    // 这样 BaseFree.vue 等组件可以在 PrompInfo 中显示详细的错误信息
    return Promise.reject(new Error(message))
  }
)

// 刷新Token
const refreshToken = (): Promise<IResponse> => {
  const authStore = useAuthStoreWithOut()
  const data = authStore.getRefreshToken
  return request.post({ url: '/auth/token/refresh', data })
}

export { service }

import request from '@/config/axios'
import type { Project, Dynamic, RadarData } from './types'

export const getProjectApi = (): Promise<IResponse<Project>> => {
  return request.get({ url: '/vadmin/workplace/project' })
}

export const getDynamicApi = (): Promise<IResponse<Dynamic[]>> => {
  return request.get({ url: '/vadmin/workplace/dynamic' })
}

export const getRadarApi = (): Promise<IResponse<RadarData[]>> => {
  return request.get({ url: '/vadmin/workplace/radar' })
}

/**
 * 图片列表处理工具
 * 
 * 用于处理图片列表字段的常见操作：
 * 1. 排序前缀处理（从数据库返回的格式：10-http://...）
 * 2. URL 后缀处理（?add、?delete、?original 等）
 */

/**
 * 图片 URL 查询参数后缀枚举
 * 用于标识图片的操作状态
 */
export enum ImageQuerySuffix {
  /** 原始图片（已存在于服务器） */
  ORIGINAL = 'original',
  /** 新增图片（待上传到服务器） */
  ADD = 'add',
  /** 删除图片（标记为删除，待从服务器删除） */
  DELETE = 'delete'
}

/**
 * 获取带查询参数的图片 URL
 * @param url - 图片 URL（不含查询参数）
 * @param suffix - 查询参数后缀
 * @returns 带查询参数的完整 URL
 * 
 * @example
 * getImageUrlWithSuffix('http://example.com/image.jpg', ImageQuerySuffix.ORIGINAL)
 * // 'http://example.com/image.jpg?original'
 */
export function getImageUrlWithSuffix(url: string, suffix: ImageQuerySuffix): string {
  if (typeof url !== 'string' || !url.length) return ''
  const cleanUrl = removeQueryParams(url)
  return cleanUrl ? `${cleanUrl}?${suffix}` : ''
}

/**
 * 移除图片 URL 的排序前缀
 * 处理格式：10-http://... -> http://...
 * 
 * @param url - 带排序前缀的 URL
 * @returns 移除前缀后的 URL
 * 
 * @example
 * removeSortPrefix('10-http://example.com/image.jpg') // 'http://example.com/image.jpg'
 * removeSortPrefix('http://example.com/image.jpg') // 'http://example.com/image.jpg'
 */
export function removeSortPrefix(url: string): string {
  if (typeof url !== 'string' || !url.length) return ''
  
  // 匹配格式：数字-URL（例如：10-http://...）
  const prefixMatch = url.match(/^\d+-(.+)$/)
  if (prefixMatch) {
    return prefixMatch[1]
  }
  
  return url
}

/**
 * 移除图片 URL 的查询参数后缀
 * 处理格式：http://example.com/image.jpg?original -> http://example.com/image.jpg
 * 
 * @param url - 带查询参数的 URL
 * @returns 移除查询参数后的 URL
 * 
 * @example
 * removeQueryParams('http://example.com/image.jpg?original') // 'http://example.com/image.jpg'
 * removeQueryParams('http://example.com/image.jpg?add') // 'http://example.com/image.jpg'
 * removeQueryParams('http://example.com/image.jpg?delete') // 'http://example.com/image.jpg'
 */
export function removeQueryParams(url: string): string {
  if (typeof url !== 'string' || !url.length) return ''
  
  const [path] = url.split('?')
  return path || ''
}

/**
 * 规范化图片 URL
 * 移除排序前缀和查询参数，添加 ?original 后缀
 * 
 * @param url - 图片 URL
 * @returns 规范化后的 URL
 * 
 * @example
 * normalizeImageUrl('10-http://example.com/image.jpg?add') // 'http://example.com/image.jpg?original'
 */
export function normalizeImageUrl(url: string): string {
  if (typeof url !== 'string' || !url.length) return ''
  
  // 1. 移除排序前缀
  let normalized = removeSortPrefix(url)
  
  // 2. 移除查询参数
  normalized = removeQueryParams(normalized)
  
  // 3. 添加 ?original 后缀
  return getImageUrlWithSuffix(normalized, ImageQuerySuffix.ORIGINAL)
}

/**
 * 检查图片 URL 是否标记为删除
 * 
 * @param url - 图片 URL
 * @returns 是否标记为删除
 * 
 * @example
 * isDeletedImage('http://example.com/image.jpg?delete') // true
 * isDeletedImage('http://example.com/image.jpg?original') // false
 */
export function isDeletedImage(url: string): boolean {
  if (typeof url !== 'string' || !url.length) return false
  return url.includes(`?${ImageQuerySuffix.DELETE}`)
}

/**
 * 清理图片数组
 * 移除已标记为删除的图片，并清理查询参数
 * 
 * @param imageArray - 图片数组
 * @param options - 选项配置
 * @param options.removeDeleted - 是否移除已标记为删除的图片，默认 true
 * @param options.removeQueryParams - 是否移除查询参数，默认 true
 * @returns 清理后的图片数组
 * 
 * @example
 * cleanImageArray(['http://example.com/img1.jpg?original', 'http://example.com/img2.jpg?delete'])
 * // ['http://example.com/img1.jpg']
 */
export function cleanImageArray(
  imageArray: any[],
  options: {
    removeDeleted?: boolean
    removeQueryParams?: boolean
  } = {}
): string[] {
  if (!Array.isArray(imageArray)) return []
  
  const { removeDeleted = true, removeQueryParams: shouldRemoveQueryParams = true } = options
  
  return imageArray
    .filter((item: any) => {
      // 过滤非字符串项
      if (typeof item !== 'string' || !item.length) return false
      
      // 如果启用，过滤掉已标记为删除的图片
      if (removeDeleted && isDeletedImage(item)) return false
      
      return true
    })
    .map((item: any) => {
      // 如果启用，移除查询参数
      if (shouldRemoveQueryParams) {
        return removeQueryParams(item)
      }
      return item
    })
}

/**
 * 处理图片列表（排序并移除排序前缀）
 * 用于处理从数据库返回的带排序前缀的图片列表
 * 
 * @param imageArray - 图片数组（可能包含排序前缀，如：['10-http://...', '20-http://...']）
 * @returns 处理后的图片数组（已排序并移除前缀）
 * 
 * @example
 * processImageList(['20-http://example.com/img2.jpg', '10-http://example.com/img1.jpg'])
 * // ['http://example.com/img1.jpg', 'http://example.com/img2.jpg']
 */
export function processImageList(imageArray: any[]): string[] {
  if (!Array.isArray(imageArray)) return []
  
  return imageArray
    .filter((item: any) => typeof item === 'string' && item.length > 0)
    .sort((a: string, b: string) => {
      // 按排序前缀排序（如果存在）
      // 如果都有前缀，按前缀数字排序；否则按字符串排序
      const aPrefix = a.match(/^(\d+)-/)
      const bPrefix = b.match(/^(\d+)-/)
      
      if (aPrefix && bPrefix) {
        return Number(aPrefix[1]) - Number(bPrefix[1])
      }
      
      // 如果只有一个有前缀，有前缀的排在前面
      if (aPrefix) return -1
      if (bPrefix) return 1
      
      // 都没有前缀，按字符串排序
      return a.localeCompare(b)
    })
    .map((item: string) => removeSortPrefix(item))
}

/**
 * 处理数据行中的图片字段
 * 根据明确的图片字段名列表处理图片字段
 * 
 * @param row - 数据行
 * @param imageFields - 图片字段名数组（必须明确指定，通常从列配置中 type === 'image' 的字段提取）
 * @param options - 选项配置
 * @param options.processList - 是否处理图片列表（排序并移除前缀），默认 true
 * @param options.cleanArray - 是否清理图片数组（移除删除标记等），默认 false
 * @returns 处理后的数据行
 * 
 * @example
 * processImageFields(
 *   { dish_images: ['10-http://...', '20-http://...'] },
 *   ['dish_images'],
 *   { processList: true }
 * )
 * // { dish_images: ['http://...', 'http://...'] }
 */
export function processImageFields(
  row: any,
  imageFields: string[],
  options: {
    processList?: boolean
    cleanArray?: boolean
  } = {}
): any {
  if (!row || typeof row !== 'object') return row
  if (!Array.isArray(imageFields) || imageFields.length === 0) return row
  
  const {
    processList = true,
    cleanArray = false
  } = options
  
  const processed = { ...row }
  
  // 只处理明确指定的图片字段
  imageFields.forEach((fieldName) => {
    if (!row.hasOwnProperty(fieldName)) return
    
    const value = row[fieldName]
    
    if (Array.isArray(value)) {
      // 处理图片数组
      if (processList) {
        processed[fieldName] = processImageList(value)
      }
      
      if (cleanArray) {
        processed[fieldName] = cleanImageArray(processed[fieldName], {
          removeDeleted: true,
          removeQueryParams: false // 如果已经 processList，查询参数可能已被移除
        })
      }
    } else if (typeof value === 'string' && value.length > 0) {
      // 处理单个图片 URL
      if (processList) {
        processed[fieldName] = removeSortPrefix(value)
      }
    }
  })
  
  return processed
}


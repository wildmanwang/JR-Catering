/**
 * 数据格式转换函数
 * 
 * 将数据集中的某个数据项转换为指定格式的文本
 * 
 * @param dataSet - 数据集（通常是api从后台获取的数据列表）
 * @param uniqueId - 唯一标识（用于查找数据项）
 * @param format - 返回格式配置
 *   - 数组，每个元素表示返回文本需要拼接的一个项目
 *   - 数组元素也是一个数组，有2个元素：
 *     - 第1个元素是数据类型：'field' | 'value'
 *     - 第2个元素是值：
 *       - 如果是 'field'，则从数据项中取该字段的值
 *       - 如果是 'value'，则直接使用该值作为固定字符串
 * @returns 拼接后的文本
 * 
 * @example
 * // 示例1：从数据项中取 name_unique 字段，加上固定字符串 '-'，再加上 status 字段
 * const format = [['field', 'name_unique'], ['value', '-'], ['field', 'status']]
 * const result = formatDataItem(dataSet, 1, format)
 * // 如果 name_unique='名称1'，status='状态1'，则返回 '名称1-状态1'
 * 
 * @example
 * // 示例2：只取一个字段
 * const format = [['field', 'name_unique']]
 * const result = formatDataItem(dataSet, 1, format)
 * // 返回 name_unique 字段的值
 * 
 * @example
 * // 示例3：固定字符串 + 字段
 * const format = [['value', '（'], ['field', 'name_unique'], ['value', '）']]
 * const result = formatDataItem(dataSet, 1, format)
 * // 如果 name_unique='名称1'，则返回 '（名称1）'
 */
export function formatDataItem(
  dataSet: any[],
  uniqueId: number | string,
  format: Array<['field' | 'value', string]>
): string {
  // 在数据集中查找指定唯一标识的数据项
  const dataItem = dataSet.find((item: any) => {
    // 支持 id 字段或其他唯一标识字段
    return item.id === uniqueId || item.value === uniqueId || String(item.id) === String(uniqueId)
  })

  // 如果找不到数据项，返回空字符串
  if (!dataItem) {
    console.warn(`未找到唯一标识为 ${uniqueId} 的数据项`)
    return ''
  }

  // 根据格式配置拼接文本
  const result = format
    .map(([type, value]) => {
      if (type === 'field') {
        // 从数据项中取字段值
        const fieldValue = dataItem[value]
        return fieldValue !== null && fieldValue !== undefined ? String(fieldValue) : ''
      } else if (type === 'value') {
        // 直接使用固定字符串
        return value
      } else {
        // 未知类型，返回空字符串
        console.warn(`未知的格式类型: ${type}`)
        return ''
      }
    })
    .filter(Boolean) // 过滤空值
    .join('') // 拼接

  return result
}

/**
 * 批量格式化数据项
 * 
 * 对数据集中的多个数据项进行格式化
 * 
 * @param dataSet - 数据集
 * @param uniqueIds - 唯一标识数组
 * @param format - 返回格式配置
 * @returns 格式化后的文本数组
 */
export function formatDataItems(
  dataSet: any[],
  uniqueIds: Array<number | string>,
  format: Array<['field' | 'value', string]>
): string[] {
  return uniqueIds.map((id) => formatDataItem(dataSet, id, format))
}


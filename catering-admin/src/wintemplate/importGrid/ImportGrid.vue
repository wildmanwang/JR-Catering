<script setup lang="tsx">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElTable, ElTableColumn, ElInput, ElInputNumber, ElSelect, ElOption, ElButton, ElMessage, ElMessageBox, ElUpload, ElImage, ElIcon, UploadProps } from 'element-plus'
import { ButtonPre } from '@/components/ButtonPre'
import { PrompInfo } from '@/components/PrompInfo'
import { Delete } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/modules/auth'

defineOptions({
  name: 'ImportGrid'
})

// ==================== 类型定义 ====================

/** 列类型 */
type ColumnType = 'text' | 'number' | 'select' | 'textarea' | 'image' | 'date' | 'datetime'

/** 下拉选项 */
interface SelectOption {
  label: string
  value: any
}

/** 表格列配置 */
export interface ImportGridColumn {
  /** 字段名 */
  field: string
  /** 列标题 */
  label: string
  /** 列类型 */
  type?: ColumnType
  /** 列宽度 */
  width?: string | number
  /** 最小宽度 */
  minWidth?: string | number
  /** 对齐方式 */
  align?: 'left' | 'center' | 'right'
  /** 是否可编辑，默认为 true */
  editable?: boolean
  /** 是否显示，默认为 true */
  show?: boolean
  /** 下拉选项（select 类型使用） */
  options?: SelectOption[] | (() => SelectOption[])
  /** 图片字段配置（image 类型使用） */
  imageField?: string // 图片数据字段名，默认使用 field
  imageDisplayField?: string // 图片显示字段名，默认使用 `${field}_display`
  /** 格式化函数 */
  formatter?: (value: any, row: any) => any
  /** 自定义渲染函数 */
  render?: (scope: any) => JSX.Element | null
}

/** 操作列配置 */
export interface ActionColumnConfig {
  /** 操作按钮配置 */
  buttons?: Array<{
    label: string
    type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text'
    onClick: (row: any, index: number) => void
    [key: string]: any
  }>
  /** 自定义操作列渲染 */
  render?: (scope: any) => JSX.Element | null
}

/** 组件 Props */
interface Props {
  /** 列配置数组 */
  columns: ImportGridColumn[]
  /** 初始数据列表（从父窗口传入） */
  initialData?: any[]
  /** 操作列配置 */
  actionColumn?: ActionColumnConfig
  /** 保存接口 */
  saveApi?: (data: any[]) => Promise<any>
  /** 创建默认行的函数 */
  createDefaultRow?: () => any
}

// ==================== Props 定义 ====================
const props = withDefaults(defineProps<Props>(), {
  initialData: () => [],
  createDefaultRow: undefined,
  actionColumn: () => ({})
})

// ==================== Emits 定义 ====================
const emit = defineEmits<{
  save: [data: any[]]
  cancel: []
  success: []
}>()

// ==================== 状态管理 ====================
const authStore = useAuthStore()
const token = computed(() => authStore.getToken)

/** 数据列表 */
const dataList = ref<any[]>([])

/** 当前正在编辑的单元格 */
const editingCell = ref<string>('')

/** 保存加载状态 */
const saveLoading = ref(false)

/** 信息提示组件引用 */
const prompInfoRef = ref<InstanceType<typeof PrompInfo>>()

// ==================== 工具函数 ====================

/**
 * 显示信息提示
 */
const showInfo = (type: 'info' | 'warn' | 'error' | null, message?: string) => {
  if (!type || !message) {
    prompInfoRef.value?.ready()
    return
  }
  if (type === 'info') {
    prompInfoRef.value?.info(message)
  } else if (type === 'warn') {
    prompInfoRef.value?.warn(message)
  } else if (type === 'error') {
    prompInfoRef.value?.err(message)
  }
}

/**
 * 创建默认行
 */
const createDefaultRow = (): any => {
  if (props.createDefaultRow) {
    return props.createDefaultRow()
  }
  // 默认实现：创建一个空对象
  const row: any = {}
  props.columns.forEach(col => {
    if (col.type === 'image') {
      const imageField = col.imageField || col.field
      const imageDisplayField = col.imageDisplayField || `${col.field}_display`
      row[imageField] = []
      row[imageDisplayField] = []
    } else {
      row[col.field] = undefined
    }
  })
  return row
}

/**
 * 获取下拉选项
 */
const getSelectOptions = (column: ImportGridColumn): SelectOption[] => {
  if (!column.options) return []
  return typeof column.options === 'function' ? column.options() : column.options
}

/**
 * 格式化单元格值
 */
const formatCellValue = (value: any, column: ImportGridColumn, row: any): any => {
  if (column.formatter) {
    return column.formatter(value, row)
  }
  if (column.type === 'select' && column.options) {
    const options = getSelectOptions(column)
    const option = options.find(opt => opt.value === value)
    return option ? option.label : value
  }
  return value
}

/**
 * 检查单元格是否正在编辑
 */
const isEditingCell = (rowIndex: number, field: string): boolean => {
  return editingCell.value === `${rowIndex}-${field}`
}

/**
 * 开始编辑单元格
 */
const startEdit = (rowIndex: number, field: string) => {
  const column = props.columns.find(col => col.field === field)
  if (!column || column.editable === false) return
  editingCell.value = `${rowIndex}-${field}`
}

/**
 * 完成编辑单元格
 */
const finishEdit = (rowIndex: number, field: string) => {
  if (editingCell.value === `${rowIndex}-${field}`) {
    editingCell.value = ''
  }
}

// ==================== 行操作 ====================

/**
 * 添加新行
 */
const handleAddRow = () => {
  const newRow = createDefaultRow()
  dataList.value.push(newRow)
  const index = dataList.value.length - 1
  showInfo('info', `已新增 1 行，共 ${dataList.value.length} 行`)
  
  // 自动聚焦到第一个可编辑字段
  nextTick(() => {
    const firstEditableColumn = props.columns.find(col => col.editable !== false)
    if (firstEditableColumn) {
      startEdit(index, firstEditableColumn.field)
    }
  })
}

/**
 * 删除行
 */
const handleDeleteRow = async (index: number) => {
  if (index < 0 || index >= dataList.value.length) return
  
  try {
    await ElMessageBox.confirm('确定要删除这一行吗？', '提示', {
      type: 'warning'
    })
    dataList.value.splice(index, 1)
    showInfo('info', `已删除 1 行，剩余 ${dataList.value.length} 行`)
  } catch {
    // 用户取消删除
  }
}

// ==================== 图片处理 ====================

/**
 * 上传文件
 */
const uploadFile = async (fileForm: FormData): Promise<{ success: boolean; data?: any; message?: string }> => {
  try {
    const res = await fetch('/api/vadmin/system/upload/image/to/local', {
      method: 'POST',
      body: fileForm,
      headers: {
        'Authorization': token.value || ''
      }
    })
    
    if (!res.ok) {
      throw new Error(`HTTP错误！状态：${res.status}`)
    }
    
    const data = await res.json()
    return {
      success: true,
      data: data
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : '未知的错误.'
    return {
      success: false,
      message: msg
    }
  }
}

/**
 * 处理图片上传
 */
const handleImageUpload = async (row: any, column: ImportGridColumn, file: File) => {
  const imageField = column.imageField || column.field
  const imageDisplayField = column.imageDisplayField || `${column.field}_display`
  
  // 确保字段存在
  if (!Array.isArray(row[imageField])) {
    row[imageField] = []
  }
  if (!Array.isArray(row[imageDisplayField])) {
    row[imageDisplayField] = []
  }
  
  // 检查文件是否已存在
  const exists = row[imageField].some((item: any) => {
    if (Array.isArray(item) && item[2] === file.name) {
      return true
    }
    return false
  })
  
  if (exists) {
    ElMessage.warning('该图片已存在')
    return
  }
  
  // 创建预览 URL
  const previewUrl = URL.createObjectURL(file)
  
  // 添加到显示列表
  row[imageDisplayField].push(previewUrl)
  
  // 添加到数据列表（格式：[previewUrl, 'add', fileName, file]）
  row[imageField].push([previewUrl, 'add', file.name, file])
}

/**
 * 处理图片删除
 */
const handleImageRemove = (row: any, column: ImportGridColumn, index: number) => {
  const imageField = column.imageField || column.field
  const imageDisplayField = column.imageDisplayField || `${column.field}_display`
  
  if (Array.isArray(row[imageField][index])) {
    // 未上传的图片，直接删除
    row[imageDisplayField].splice(index, 1)
    row[imageField].splice(index, 1)
  } else {
    // 已上传的图片，标记为删除
    const display = row[imageDisplayField][index]
    const stored = row[imageField][index]
    if (typeof display === 'string') {
      row[imageDisplayField][index] = `${display.split('?')[0]}?delete`
    }
    if (typeof stored === 'string') {
      row[imageField][index] = `${stored.split('?')[0]}?delete`
    }
  }
}

/**
 * 处理图片拖拽排序
 */
const handleImageDragDrop = (row: any, column: ImportGridColumn, sourceIndex: number, targetIndex: number) => {
  const imageField = column.imageField || column.field
  const imageDisplayField = column.imageDisplayField || `${column.field}_display`
  
  if (sourceIndex !== targetIndex && sourceIndex >= 0 && targetIndex >= 0) {
    const imagesDisplay = [...row[imageDisplayField]]
    const [movedItem1] = imagesDisplay.splice(sourceIndex, 1)
    imagesDisplay.splice(targetIndex, 0, movedItem1)
    row[imageDisplayField] = imagesDisplay
    
    const imagesData = [...row[imageField]]
    const [movedItem2] = imagesData.splice(sourceIndex, 1)
    imagesData.splice(targetIndex, 0, movedItem2)
    row[imageField] = imagesData
  }
}

// ==================== 保存处理 ====================

/**
 * 处理图片字段上传
 */
const processImageUploads = async (data: any[]): Promise<void> => {
  for (const row of data) {
    for (const column of props.columns) {
      if (column.type === 'image') {
        const imageField = column.imageField || column.field
        const imageDisplayField = column.imageDisplayField || `${column.field}_display`
        
        if (!row[imageField] || !Array.isArray(row[imageField])) {
          continue
        }
        
        // 处理每个图片项
        for (let index = 0; index < row[imageField].length; index++) {
          const fileData = row[imageField][index]
          
          // 如果是数组格式（包含文件对象），说明是未上传的图片，需要上传
          if (Array.isArray(fileData)) {
            const fileForm = new FormData()
            fileForm.append('file', fileData[3].raw)
            fileForm.append('path', 'system')
            const res = await uploadFile(fileForm)
            if (!res.success) {
              throw new Error(`图片上传错误：${res.message}`)
            }
            // 转换为字符串格式：路径 + 操作类型（add/delete）
            row[imageField][index] = `${res.data.data.remote_path}?${fileData[1]}`
            row[imageDisplayField][index] = `${res.data.data.remote_path}?${fileData[1]}`
          }
          // 如果已经是字符串格式，保持不变
        }
      }
    }
  }
}

/**
 * 处理保存
 */
const handleSave = async () => {
  if (dataList.value.length === 0) {
    showInfo('warn', '没有数据需要保存')
    return
  }
  
  saveLoading.value = true
  try {
    // 处理图片上传
    await processImageUploads(dataList.value)
    
    // 调用保存接口
    if (props.saveApi) {
      await props.saveApi(dataList.value)
      showInfo('info', '保存成功')
      emit('success')
    } else {
      // 如果没有提供保存接口，触发 save 事件
      emit('save', dataList.value)
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '保存失败'
    showInfo('error', errorMessage)
  } finally {
    saveLoading.value = false
  }
}

/**
 * 处理取消
 */
const handleCancel = () => {
  emit('cancel')
}

// ==================== 列渲染函数 ====================

/**
 * 渲染文本列
 */
const renderTextColumn = (column: ImportGridColumn) => {
  return (
    <ElTableColumn
      prop={column.field}
      label={column.label}
      width={column.width}
      min-width={column.minWidth}
      align={column.align || 'left'}
      show-overflow-tooltip
    >
      {{
        default: (scope: any) => {
          const rowIndex = scope.$index
          const isEditing = isEditingCell(rowIndex, column.field)
          const value = scope.row[column.field]
          
          if (column.editable !== false && isEditing) {
            return (
              <ElInput
                v-model={scope.row[column.field]}
                onBlur={() => finishEdit(rowIndex, column.field)}
                onKeydown={(e: KeyboardEvent) => {
                  if (e.key === 'Enter' || e.key === 'Tab') {
                    e.preventDefault()
                    finishEdit(rowIndex, column.field)
                  }
                }}
                data-cell-key={`${rowIndex}-${column.field}`}
              />
            )
          }
          
          return (
            <span
              onClick={() => column.editable !== false && startEdit(rowIndex, column.field)}
              style={{ cursor: column.editable !== false ? 'pointer' : 'default' }}
            >
              {formatCellValue(value, column, scope.row) || ''}
            </span>
          )
        }
      }}
    </ElTableColumn>
  )
}

/**
 * 渲染数字列
 */
const renderNumberColumn = (column: ImportGridColumn) => {
  return (
    <ElTableColumn
      prop={column.field}
      label={column.label}
      width={column.width}
      min-width={column.minWidth}
      align={column.align || 'right'}
      show-overflow-tooltip
    >
      {{
        default: (scope: any) => {
          const rowIndex = scope.$index
          const isEditing = isEditingCell(rowIndex, column.field)
          const value = scope.row[column.field]
          
          if (column.editable !== false && isEditing) {
            return (
              <ElInputNumber
                v-model={scope.row[column.field]}
                onBlur={() => finishEdit(rowIndex, column.field)}
                onKeydown={(e: KeyboardEvent) => {
                  if (e.key === 'Enter' || e.key === 'Tab') {
                    e.preventDefault()
                    finishEdit(rowIndex, column.field)
                  }
                }}
                data-cell-key={`${rowIndex}-${column.field}`}
                style="width: 100%"
              />
            )
          }
          
          return (
            <span
              onClick={() => column.editable !== false && startEdit(rowIndex, column.field)}
              style={{ cursor: column.editable !== false ? 'pointer' : 'default' }}
            >
              {formatCellValue(value, column, scope.row) || ''}
            </span>
          )
        }
      }}
    </ElTableColumn>
  )
}

/**
 * 渲染下拉列
 */
const renderSelectColumn = (column: ImportGridColumn) => {
  return (
    <ElTableColumn
      prop={column.field}
      label={column.label}
      width={column.width}
      min-width={column.minWidth}
      align={column.align || 'left'}
      show-overflow-tooltip
    >
      {{
        default: (scope: any) => {
          const rowIndex = scope.$index
          const isEditing = isEditingCell(rowIndex, column.field)
          const value = scope.row[column.field]
          const options = getSelectOptions(column)
          
          if (column.editable !== false && isEditing) {
            return (
              <ElSelect
                v-model={scope.row[column.field]}
                onBlur={() => finishEdit(rowIndex, column.field)}
                onKeydown={(e: KeyboardEvent) => {
                  if (e.key === 'Enter' || e.key === 'Tab') {
                    e.preventDefault()
                    finishEdit(rowIndex, column.field)
                  }
                }}
                data-cell-key={`${rowIndex}-${column.field}`}
                style="width: 100%"
                placeholder="请选择"
              >
                {options.map(option => (
                  <ElOption key={option.value} label={option.label} value={option.value} />
                ))}
              </ElSelect>
            )
          }
          
          return (
            <span
              onClick={() => column.editable !== false && startEdit(rowIndex, column.field)}
              style={{ cursor: column.editable !== false ? 'pointer' : 'default' }}
            >
              {formatCellValue(value, column, scope.row) || ''}
            </span>
          )
        }
      }}
    </ElTableColumn>
  )
}

/**
 * 渲染文本域列
 */
const renderTextareaColumn = (column: ImportGridColumn) => {
  return (
    <ElTableColumn
      prop={column.field}
      label={column.label}
      width={column.width}
      min-width={column.minWidth}
      align={column.align || 'left'}
      show-overflow-tooltip
    >
      {{
        default: (scope: any) => {
          const rowIndex = scope.$index
          const isEditing = isEditingCell(rowIndex, column.field)
          const value = scope.row[column.field]
          
          if (column.editable !== false && isEditing) {
            return (
              <ElInput
                v-model={scope.row[column.field]}
                type="textarea"
                onBlur={() => finishEdit(rowIndex, column.field)}
                data-cell-key={`${rowIndex}-${column.field}`}
                style="width: 100%"
                autosize={{ minRows: 2, maxRows: 4 }}
              />
            )
          }
          
          return (
            <span
              onClick={() => column.editable !== false && startEdit(rowIndex, column.field)}
              style={{ cursor: column.editable !== false ? 'pointer' : 'default' }}
            >
              {formatCellValue(value, column, scope.row) || ''}
            </span>
          )
        }
      }}
    </ElTableColumn>
  )
}

/**
 * 渲染图片列
 */
const renderImageColumn = (column: ImportGridColumn) => {
  const imageField = column.imageField || column.field
  const imageDisplayField = column.imageDisplayField || `${column.field}_display`
  
  return (
    <ElTableColumn
      prop={column.field}
      label={column.label}
      width={column.width || '320px'}
      min-width={column.minWidth}
      align={column.align || 'left'}
    >
      {{
        default: (scope: any) => {
          const row = scope.row
          const rowIndex = scope.$index
          
          // 确保字段存在
          if (!Array.isArray(row[imageField])) {
            row[imageField] = []
          }
          if (!Array.isArray(row[imageDisplayField])) {
            row[imageDisplayField] = []
          }
          
          const images = row[imageDisplayField] || []
          const dragState = reactive({
            dragIndex: -1,
            dragOverIndex: -1
          })
          
          const beforeUpload: UploadProps['beforeUpload'] = (rawFile) => {
            const isImage = ['image/jpeg', 'image/gif', 'image/png'].includes(rawFile.type)
            const isLtSize = rawFile.size / 1024 / 1024 < 2
            if (!isImage) {
              ElMessage.error('上传图片必须是 JPG/GIF/PNG 格式!')
              return false
            }
            if (!isLtSize) {
              ElMessage.error('上传图片大小不能超过2MB!')
              return false
            }
            return true
          }
          
          const handleFileChange: UploadProps['onChange'] = (file) => {
            if (file.raw) {
              handleImageUpload(row, column, file.raw)
            }
          }
          
          const handleRemove = (index: number) => {
            handleImageRemove(row, column, index)
          }
          
          const handleDragStart = (index: number, event: DragEvent) => {
            dragState.dragIndex = index
            event.dataTransfer!.effectAllowed = 'move'
            event.dataTransfer!.setData('text/plain', index.toString())
          }
          
          const handleDragOver = (event: DragEvent) => {
            event.preventDefault()
            event.dataTransfer!.dropEffect = 'move'
          }
          
          const handleDragEnter = (index: number, event: DragEvent) => {
            event.preventDefault()
            dragState.dragOverIndex = index
          }
          
          const handleDragLeave = () => {
            dragState.dragOverIndex = -1
          }
          
          const handleDrop = (targetIndex: number, event: DragEvent) => {
            event.preventDefault()
            const sourceIndex = parseInt(event.dataTransfer!.getData('text/plain'))
            if (sourceIndex !== targetIndex && sourceIndex >= 0 && targetIndex >= 0) {
              handleImageDragDrop(row, column, sourceIndex, targetIndex)
            }
            dragState.dragIndex = -1
            dragState.dragOverIndex = -1
          }
          
          const getPreviewUrl = (image: any): string => {
            if (typeof image === 'string') {
              const [path] = image.split('?')
              return path || image
            }
            if (Array.isArray(image)) {
              return image[0] || ''
            }
            return ''
          }
          
          const getPreviewList = (): string[] => {
            return images
              .map((img: any) => getPreviewUrl(img))
              .filter((url: string) => url && !url.endsWith('?delete'))
          }
          
          return (
            <div class="import-grid-image-cell">
              <div class="image-list">
                {images.map((image: any, index: number) => {
                  const previewUrl = getPreviewUrl(image)
                  const isDeleted = typeof image === 'string' && image.endsWith('?delete')
                  
                  if (isDeleted) return null
                  
                  return (
                    <div
                      key={index}
                      class={['image-item', dragState.dragOverIndex === index ? 'drag-over' : '']}
                      draggable={column.editable !== false}
                      onDragstart={(e: DragEvent) => handleDragStart(index, e)}
                      onDragover={handleDragOver}
                      onDragenter={(e: DragEvent) => handleDragEnter(index, e)}
                      onDragleave={handleDragLeave}
                      onDrop={(e: DragEvent) => handleDrop(index, e)}
                    >
                      <ElImage
                        src={previewUrl}
                        fit="cover"
                        preview-src-list={getPreviewList()}
                        preview-teleported={true}
                        style="width: 60px; height: 60px; border-radius: 4px;"
                      />
                      {column.editable !== false && (
                        <div class="image-actions">
                          <ElIcon
                            class="delete-icon"
                            onClick={() => handleRemove(index)}
                          >
                            <Delete />
                          </ElIcon>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
              {column.editable !== false && images.length < 10 && (
                <ElUpload
                  before-upload={beforeUpload}
                  onChange={handleFileChange}
                  show-file-list={false}
                  accept="image/*"
                >
                  <ElButton type="primary" size="small" style="margin-top: 8px;">
                    上传图片
                  </ElButton>
                </ElUpload>
              )}
            </div>
          )
        }
      }}
    </ElTableColumn>
  )
}

/**
 * 渲染操作列
 */
const renderActionColumn = () => {
  return (
    <ElTableColumn
      label="操作"
      width={props.actionColumn?.buttons?.length ? `${(props.actionColumn.buttons.length * 80 + 40)}px` : '120px'}
      align="center"
      fixed="right"
    >
      {{
        default: (scope: any) => {
          const rowIndex = scope.$index
          
          // 如果提供了自定义渲染函数，使用自定义渲染
          if (props.actionColumn?.render) {
            return props.actionColumn.render(scope)
          }
          
          // 默认操作按钮：删除
          const defaultButtons = [
            {
              label: '删除',
              type: 'danger' as const,
              onClick: () => handleDeleteRow(rowIndex)
            }
          ]
          
          // 合并默认按钮和配置的按钮
          const buttons = props.actionColumn?.buttons || defaultButtons
          
          return (
            <div class="import-grid-action-cell">
              {buttons.map((btn, index) => (
                <ElButton
                  key={index}
                  type={btn.type || 'primary'}
                  size="small"
                  link
                  onClick={() => btn.onClick(scope.row, rowIndex)}
                  {...btn}
                >
                  {btn.label}
                </ElButton>
              ))}
            </div>
          )
        }
      }}
    </ElTableColumn>
  )
}

/**
 * 渲染列
 */
const renderColumn = (column: ImportGridColumn) => {
  if (column.show === false) {
    return null
  }
  
  // 如果提供了自定义渲染函数，使用自定义渲染
  if (column.render) {
    return (
      <ElTableColumn
        prop={column.field}
        label={column.label}
        width={column.width}
        min-width={column.minWidth}
        align={column.align || 'left'}
      >
        {{
          default: (scope: any) => column.render!(scope)
        }}
      </ElTableColumn>
    )
  }
  
  // 根据列类型渲染
  switch (column.type) {
    case 'number':
      return renderNumberColumn(column)
    case 'select':
      return renderSelectColumn(column)
    case 'textarea':
      return renderTextareaColumn(column)
    case 'image':
      return renderImageColumn(column)
    case 'text':
    default:
      return renderTextColumn(column)
  }
}

// ==================== 初始化 ====================

/**
 * 初始化数据
 */
const initData = () => {
  if (props.initialData && props.initialData.length > 0) {
    dataList.value = props.initialData.map(item => ({
      ...createDefaultRow(),
      ...item
    }))
    showInfo('info', `已载入 ${dataList.value.length} 条记录`)
  } else {
    dataList.value = [createDefaultRow()]
    showInfo(null)
  }
}

// 监听 initialData 变化
watch(() => props.initialData, () => {
  initData()
}, { immediate: true, deep: true })

// ==================== 暴露方法 ====================
defineExpose({
  getData: () => dataList.value,
  addRow: handleAddRow,
  showInfo
})
</script>

<template>
  <div class="import-grid-wrapper">
    <!-- 顶部工具栏 -->
    <div class="import-grid-toolbar">
      <div class="toolbar-left">
        <ButtonPre stype="new" @click="handleAddRow" />
        <slot name="toolbar-left"></slot>
      </div>
      
      <div class="toolbar-info">
        <PrompInfo ref="prompInfoRef" />
      </div>
      
      <div class="toolbar-right">
        <ButtonPre
          stype="save"
          :loading="saveLoading"
          @click="handleSave"
        />
        <ButtonPre
          stype="return"
          @click="handleCancel"
        />
        <slot name="toolbar-right"></slot>
      </div>
    </div>
    
    <!-- 表格区域 -->
    <div class="import-grid-table">
      <ElTable
        :data="dataList"
        border
        stripe
        style="width: 100%"
      >
        <!-- 渲染配置的列 -->
        <template v-for="column in columns" :key="column.field">
          <component :is="() => renderColumn(column)" />
        </template>
        
        <!-- 固定操作列 -->
        <component :is="() => renderActionColumn()" />
      </ElTable>
    </div>
  </div>
</template>

<style scoped lang="less">
.import-grid-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.import-grid-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 0;
  gap: 10px;
  flex-shrink: 0;
  
  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }
  
  .toolbar-info {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: center;
  }
  
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }
}

.import-grid-table {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

.import-grid-image-cell {
  .image-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    
    .image-item {
      position: relative;
      cursor: move;
      
      &:hover .image-actions {
        opacity: 1;
      }
      
      &.drag-over {
        border: 2px dashed #409eff;
      }
      
      .image-actions {
        position: absolute;
        top: 0;
        right: 0;
        opacity: 0;
        transition: opacity 0.3s;
        
        .delete-icon {
          background: rgba(0, 0, 0, 0.5);
          color: white;
          padding: 4px;
          border-radius: 4px;
          cursor: pointer;
          
          &:hover {
            background: rgba(0, 0, 0, 0.7);
          }
        }
      }
    }
  }
}

.import-grid-action-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* 移除按钮默认 margin */
:deep(.my-button) {
  margin: 0 !important;
}
</style>


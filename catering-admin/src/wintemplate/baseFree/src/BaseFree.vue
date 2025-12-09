<script setup lang="tsx">
import { computed, ref, watch, unref, nextTick } from 'vue'
import { ElDrawer, ElScrollbar, ElTabs, ElTabPane, ElMessage, ElMessageBox, ElUpload, UploadProps, ElIcon, ElImage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { ButtonPre } from '@/components/ButtonPre'
import { PrompInfo } from '@/components/PrompInfo'
import { Form, FormSchema } from '@/components/Form'
import { useForm } from '@/hooks/web/useForm'
import { useAuthStore } from '@/store/modules/auth'

defineOptions({
  name: 'BaseFree'
})

// ==================== 类型定义 ====================
/** 表单字段配置 */
export interface FreeFormField extends FormSchema {
  /** 列类型，用于决定列的显示样式和处理逻辑 */
  type?: 'image' | 'text' | 'status' | 'number' | 'select' | 'dropdown'
  // 自定义字段转换函数：如果提供，将使用此函数替代模板的默认处理
  // 参数：field（字段配置）、data（表单数据）、mode（模式）
  // 返回：FormSchema 或 null（null 表示使用模板默认处理）
  customConvert?: (field: FreeFormField, data: any, mode: 'add' | 'edit' | 'view') => FormSchema | null
}

/** Tab 配置 */
export interface FreeTab {
  label: string // Tab 标签
  name: string // Tab 名称
  fields?: string[] // 字段列表，为空时显示所有字段
  customContent?: boolean // 是否使用自定义内容（如果为 true，将使用插槽内容）
}

/** 组件 Props */
interface Props {
  modelValue: boolean // 抽屉显示状态
  title?: string // 抽屉标题（如果提供，将直接使用此标题，忽略 pageTitle）
  pageTitle?: string // 主窗口标题（例如："菜品"）
  mode?: 'add' | 'edit' | 'view' // 模式：新增、修改、查看
  width?: string | number // 抽屉宽度
  saveLoading?: boolean // 保存按钮加载状态
  showFooter?: boolean // 是否显示底部按钮
  closeOnClickModal?: boolean // 点击遮罩是否关闭，默认 true
  // 表单相关
  formSchema: FreeFormField[] // 表单字段配置
  rules?: Record<string, any> // 表单验证规则
  currentRow?: any // 当前行数据（编辑/查看时使用）
  // 数据接口
  submitApi?: (data: any) => Promise<any> // 提交接口（新增/编辑）
  // Tab 配置
  tabs?: FreeTab[] // Tab 配置，fields 为空时显示所有字段
  // 扩展钩子函数
  beforeSubmit?: (data: any) => Promise<any> | any // 提交前的数据处理钩子
  afterInit?: (data: any) => void // 初始化后的钩子
  customFieldConvert?: (field: FreeFormField, data: any) => FormSchema | null // 全局字段转换函数
  // 选项数据映射（字段名 -> 选项数组），用于从主窗口传递下拉框选项，避免重复请求
  fieldOptions?: Record<string, any[] | (() => any[])> // 字段选项数据映射
}

// ==================== Props 定义 ====================
const props = withDefaults(defineProps<Props>(), {
  mode: 'add',
  width: '700px',
  saveLoading: false,
  showFooter: false,
  closeOnClickModal: true,
  rules: () => ({}),
  currentRow: () => null,
  tabs: () => [
    { label: '基础信息', name: 'basic' },
    { label: '操作日志', name: 'log' }
  ]
})

// ==================== Emits 定义 ====================
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'save': [data: any] // 保存事件，返回表单数据
  'cancel': [] // 取消事件
  'success': [] // 提交成功事件
}>()

// ==================== Store ====================
const authStore = useAuthStore()
const token = computed(() => authStore.getToken)

// ==================== 计算属性 ====================
/** 抽屉显示状态 */
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit('update:modelValue', val)
  }
})

/** 抽屉关闭前的回调（用于拦截关闭操作） */
const handleBeforeClose = async (done: () => void) => {
  // 如果数据已被修改，且不是查看模式，显示确认对话框
  if (isFormModified.value && props.mode !== 'view') {
    try {
      await ElMessageBox.confirm('数据未保存，要退出吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      // 用户确认退出，关闭抽屉
      isFormModified.value = false
      initialFormData.value = null
      done()
    } catch {
      // 用户取消，不关闭抽屉（不调用 done）
      return
    }
  } else {
    // 没有修改或查看模式，直接关闭
    done()
  }
}

/** 抽屉标题 */
const drawerTitle = computed(() => {
  // 如果提供了 title，直接使用（优先级最高）
  if (props.title) {
    return props.title
  }
  
  // 根据模式生成操作方式
  const operationMap = {
    add: '新增',
    edit: '修改',
    view: '查看'
  }
  const operation = operationMap[props.mode] || '操作'
  
  // 如果提供了 pageTitle，返回 "主窗口标题 - 操作方式"
  if (props.pageTitle) {
    return `${props.pageTitle} - ${operation}`
  }
  
  // 否则只返回操作方式
  return operation
})

/** 是否只读模式（查看模式） */
const isViewMode = computed(() => props.mode === 'view')

/** 是否显示保存按钮 */
const showSaveButton = computed(() => !isViewMode.value)

/** 计算抽屉宽度：左侧留600px，最小700px */
const drawerWidth = computed(() => {
  const defaultWidth = '700px'
  if (props.width) {
    if (typeof props.width === 'string' && props.width !== defaultWidth) {
      return props.width
    }
    if (typeof props.width === 'number') {
      return props.width
    }
  }
  return 'calc(100vw - 600px)'
})

// ==================== Tab 管理 ====================
/** 根据模式过滤后的 Tab 列表（新增模式下隐藏操作日志） */
const filteredTabs = computed(() => {
  if (props.mode === 'add') {
    return props.tabs.filter(tab => tab.name !== 'log')
  }
  return props.tabs
})

const activeTab = ref('basic')

// 监听模式变化和过滤后的 tabs，确保 activeTab 始终有效
watch([() => props.mode, filteredTabs], ([, tabs]) => {
  if (tabs.length > 0) {
    const currentTabExists = tabs.find(tab => tab.name === activeTab.value)
    if (!currentTabExists) {
      activeTab.value = tabs[0].name
    }
  }
}, { immediate: true })

// ==================== 表单处理 ====================
const { formRegister, formMethods } = useForm()
const { getFormData, setValues, getElFormExpose } = formMethods

// 表单注册状态
const isFormRegistered = ref(false)

// 表单数据是否被修改（用于关闭前提示）
const isFormModified = ref(false)
// 初始表单数据（用于比较是否有修改）
const initialFormData = ref<any>(null)

// 表单实例引用（用于监听表单数据变化）
const formInstanceRef = ref<any>(null)

// 表单注册回调
const handleFormRegister = (formRef: any, elFormRef: any) => {
  formRegister(formRef, elFormRef)
  formInstanceRef.value = formRef
  isFormRegistered.value = true
  // 表单注册后，初始化数据
  nextTick(() => {
    initFormData()
  })
}

/**
 * 转换表单字段配置，处理特殊字段类型
 * 确保与 Dish/components/Response.vue 的字段转换逻辑和样式保持一致
 */
const convertFormSchema = (schema: FreeFormField[]): FormSchema[] => {
  return schema.map((field) => {
    // ==================== 扩展点1：字段级别的自定义转换 ====================
    // 优先使用字段自身的 customConvert
    if (field.customConvert) {
      const customResult = field.customConvert(field, props.currentRow || {}, props.mode)
      if (customResult !== null) {
        return customResult
      }
      // 如果返回 null，继续使用模板默认处理
    }
    
    // ==================== 扩展点2：全局自定义字段转换 ====================
    // 如果提供了全局转换函数，优先使用
    if (props.customFieldConvert) {
      const globalResult = props.customFieldConvert(field, props.currentRow || {})
      if (globalResult !== null) {
        return globalResult
      }
    }
    
    let baseField: FormSchema & { type?: string } = {
      ...field,
      type: field.type,
      componentProps: field.componentProps ? {
        ...field.componentProps,
        // 设置默认样式：width: 100%（如果未定义或未设置 width）
        style: {
          width: '100%',
          ...(field.componentProps.style || {})
        },
        // 只在查看模式下禁用，保留原有的 disabled 设置
        disabled: isViewMode.value || field.componentProps?.disabled || false
      } : {
        style: {
          width: '100%'
        },
        disabled: isViewMode.value || false
      }
    }
    
    // ==================== 选项数据处理：优先使用主窗口传入的选项数据 ====================
    // 如果主窗口提供了该字段的选项数据，优先使用主窗口的数据，避免重复请求
    if (props.fieldOptions && props.fieldOptions[field.field]) {
      const optionsData = props.fieldOptions[field.field]
      const options = typeof optionsData === 'function' ? optionsData() : optionsData
      baseField = {
        ...baseField,
        componentProps: {
          ...baseField.componentProps,
          options: options
        },
        optionApi: undefined // 移除 optionApi，避免重复请求
      }
    }

    // 处理图片字段
    if (field.type === 'image') {
      return {
        ...baseField,
        formItemProps: {
          ...field.formItemProps,
          slots: {
            default: (data: any) => {
              const imageField = field.field
              const imageDisplayField = `${field.field}_display`

              if (!data[imageField]) {
                data[imageField] = unref([])
                data[imageDisplayField] = unref([])
              }

              const beforeImageUpload: UploadProps['beforeUpload'] = (rawFile) => {
                const isImage = ['image/jpeg', 'image/gif', 'image/png'].includes(rawFile.type)
                const isLtSize = rawFile.size / 1024 / 1024 < 2
                if (!isImage) {
                  ElMessage.error('上传图片必须是 JPG/GIF/PNG/ 格式!')
                }
                if (!isLtSize) {
                  ElMessage.error('上传图片大小不能超过2MB!')
                }
                return isImage && isLtSize
              }

              const handleFileChange: UploadProps['onChange'] = (file) => {
                if (file.raw) {
                  const exists = data[imageField].some((item: any) => item[2] === file.name)
                  if (!exists) {
                    const previewUrl = URL.createObjectURL(file.raw)
                    data[imageDisplayField].push(previewUrl)
                    data[imageField].push([previewUrl, 'add', file.name, file])
                  }
                }
              }

              const handleremoveimage = (index: number) => {
                if (Array.isArray(data[imageField][index])) {
                  data[imageDisplayField].splice(index, 1)
                  data[imageField].splice(index, 1)
                } else {
                  data[imageDisplayField][index] = `${data[imageDisplayField][index].split('?')[0]}?delete`
                  data[imageField][index] = `${data[imageField][index].split('?')[0]}?delete`
                }
              }

              const dragIndex = ref(-1)
              const dragOverIndex = ref(-1)

              const handleDragStart = (index: number, event: DragEvent) => {
                dragIndex.value = index
                event.dataTransfer!.effectAllowed = 'move'
                event.dataTransfer!.setData('text/plain', index.toString())
                setTimeout(() => {
                  (event.target as HTMLElement).classList.add('dragging')
                }, 0)
              }

              const handleDragOver = (event: DragEvent) => {
                event.preventDefault()
                event.dataTransfer!.dropEffect = 'move'
              }

              const handleDragEnter = (index: number, event: DragEvent) => {
                event.preventDefault()
                dragOverIndex.value = index
              }

              const handleDragLeave = (event: DragEvent) => {
                if (!(event.currentTarget as HTMLElement).contains(event.relatedTarget as HTMLElement)) {
                  dragOverIndex.value = -1
                }
              }

              const handleDrop = (targetIndex: number, event: DragEvent) => {
                event.preventDefault()
                const sourceIndex = parseInt(event.dataTransfer!.getData('text/plain'))
                if (sourceIndex !== targetIndex && sourceIndex >= 0 && targetIndex >= 0) {
                  const images_display = [...data[imageDisplayField]]
                  const [movedItem1] = images_display.splice(sourceIndex, 1)
                  images_display.splice(targetIndex, 0, movedItem1)
                  data[imageDisplayField] = images_display

                  const images_data = [...data[imageField]]
                  const [movedItem2] = images_data.splice(sourceIndex, 1)
                  images_data.splice(targetIndex, 0, movedItem2)
                  data[imageField] = images_data
                }
                dragIndex.value = -1
                dragOverIndex.value = -1
              }

              const handleDragEnd = () => {
                dragIndex.value = -1
                dragOverIndex.value = -1
                const draggingElements = document.querySelectorAll('.dragging')
                draggingElements.forEach(el => {
                  el.classList.remove('dragging')
                })
              }

              /**
               * 生成预览列表：过滤掉删除标记和 OSS 参数
               */
              const generatePreviewList = (): string[] => {
                if (!data[imageDisplayField] || !Array.isArray(data[imageDisplayField])) {
                  return []
                }
                return data[imageDisplayField]
                  .filter((img: string) => img && !img.endsWith('?delete'))
                  .map((img: string) => {
                    // 移除 OSS 参数，使用原始图片进行预览
                    if (typeof img === 'string' && img.includes('?')) {
                      const [path] = img.split('?')
                      return path || img
                    }
                    return img
                  })
                  .filter(Boolean)
              }

              const previewList = generatePreviewList()

              /**
               * 图片加载失败处理
               */
              const handleError = (e: Event) => {
                const img = e.target as HTMLImageElement
                if (img && img.src) {
                  // 图片加载失败时的处理逻辑
                }
              }

              // 是否为查看模式
              const isView = isViewMode.value

              return (
                <div class="image-container">
                  {data[imageDisplayField]?.map((image: string, index: number) => (
                    image && !image.endsWith('?delete') && (
                      <div
                        key={`${index}-${image}`}
                        class={`image-group ${!isView && dragIndex.value === index ? 'dragging' : ''} ${!isView && dragOverIndex.value === index ? 'drag-over' : ''}`}
                        onClick={(e) => { e.stopPropagation(); }}
                        draggable={!isView}
                        onDragstart={!isView ? (e) => handleDragStart(index, e) : undefined}
                        onDragover={!isView ? handleDragOver : undefined}
                        onDragenter={!isView ? (e) => handleDragEnter(index, e) : undefined}
                        onDragleave={!isView ? handleDragLeave : undefined}
                        onDrop={!isView ? (e) => handleDrop(index, e) : undefined}
                        onDragend={!isView ? handleDragEnd : undefined}
                      >
                        <ElImage
                          src={image}
                          class="image-item"
                          onError={handleError}
                          zoom-rate={1.2}
                          preview-src-list={previewList.length > 0 ? previewList : []}
                          preview-teleported={true}
                          hide-on-click-modal={true}
                          initial-index={index}
                          fit="cover"
                          style="width: 100%; height: 100%;"
                        />
                        {!isView && (
                          <div onClick={(e) => { e.stopPropagation(); handleremoveimage(index);}} class="remove-btn">x</div>
                        )}
                      </div>
                    )
                  ))}
                  {!isView && (
                    <div class="image-group-uploader">
                      {(!data[imageDisplayField] || data[imageDisplayField]?.length < 10) && (
                        <ElUpload
                          action="/api/vadmin/system/upload/image/to/local"
                          data={{ path: 'system' }}
                          show-file-list={false}
                          multiple={true}
                          auto-upload={false}
                          before-upload={beforeImageUpload}
                          on-change={handleFileChange}
                          accept="image/jpeg,image/gif,image/png"
                          name="file"
                          drag={true}
                          headers={{ Authorization: token.value }}
                          limit={10}
                        >
                          <div>
                            <ElIcon class="el-icon--upload"><UploadFilled /></ElIcon>
                            <div class="upload-text">拖拽文件到此或点击上传</div>
                          </div>
                        </ElUpload>
                      )}
                    </div>
                  )}
                </div>
              )
            }
          }
        }
      }
    }

    return baseField
  })
}

/** 转换后的表单字段配置 */
const convertedFormSchema = computed(() => convertFormSchema(props.formSchema))

/**
 * 根据当前 Tab 过滤字段
 */
const getFieldsByTab = (tabName: string) => {
  const tab = props.tabs.find(t => t.name === tabName)
  if (!tab || !tab.fields || tab.fields.length === 0) {
    return convertedFormSchema.value
  }
  return convertedFormSchema.value.filter(field => tab.fields!.includes(field.field))
}

// ==================== 数据初始化 ====================
/**
 * 初始化表单数据
 */
const initFormData = async () => {
  // 等待表单注册完成
  await nextTick()
  
  let formData: any = {}
  
  if (props.currentRow && (props.mode === 'edit' || props.mode === 'view')) {
    formData = { ...props.currentRow }
    props.formSchema.forEach(field => {
      if (field.type === 'image') {
        const imageField = field.field
        const imageDisplayField = `${field.field}_display`
        if (formData[imageField] && Array.isArray(formData[imageField])) {
          // 编辑模式下，对图片进行排序并标记为 original（参考 Dish.vue 第537-540行）
          if (props.mode === 'edit') {
            // 排序图片（参考 Dish.vue 第537行）
            formData[imageField].sort((a: string, b: string) => a.localeCompare(b))
            // 提取图片路径（参考 Dish.vue 第538行：item.split('-')[1]）
            formData[imageField] = formData[imageField].map((item: string) => {
              if (item.includes('-')) {
                return item.split('-')[1]
              }
              // 如果包含 '?'，提取前面的部分（移除已有标记）
              if (item.includes('?')) {
                return item.split('?')[0]
              }
              return item
            })
            // 设置显示字段（参考 Dish.vue 第539行）
            formData[imageDisplayField] = [...formData[imageField]]
            // 标记为 original（参考 Dish.vue 第540行）
            formData[imageField] = formData[imageField].map((item: string) => `${item}?original`)
          } else {
            // 查看模式下，直接设置显示字段
            formData[imageDisplayField] = formData[imageField].map((img: any) => {
              if (typeof img === 'string') {
                // 移除标记，只显示路径
                return img.includes('?') ? img.split('?')[0] : img
              }
              if (Array.isArray(img) && img.length > 0) {
                return img[0]
              }
              return img
            })
          }
        }
      }
    })
    await setValues(formData)
  } else {
    // 新增模式：应用字段默认值
    formData = {}
    
    props.formSchema.forEach(field => {
      if (field.value !== undefined) {
        formData[field.field] = field.value
      }
    })
    
    await setValues(formData)
  }
  
  // ==================== 扩展点4：初始化后的钩子 ====================
  if (props.afterInit) {
    props.afterInit(formData)
  }
  
  // 保存初始表单数据，用于后续比较是否有修改
  initialFormData.value = JSON.parse(JSON.stringify(formData))
  isFormModified.value = false
}

// 监听 currentRow 变化（仅在表单已注册时更新）
watch(() => props.currentRow, () => {
  if (isFormRegistered.value) {
    initFormData()
  }
}, { deep: true })

// 监听 drawerVisible 变化，关闭时清空表单
watch(() => drawerVisible.value, async (val) => {
  if (!val) {
    // 抽屉关闭时，重置状态
    isFormRegistered.value = false
    isFormModified.value = false
    initialFormData.value = null
  } else {
    // 抽屉打开时，重置注册状态，等待表单注册
    isFormRegistered.value = false
    isFormModified.value = false
    initialFormData.value = null
  }
})

// 监听表单数据变化，标记为已修改（仅在新增和编辑模式下）
watch(() => {
  if (!isFormRegistered.value || !formInstanceRef.value || props.mode === 'view') {
    return null
  }
  // 直接访问表单实例的 formModel
  return formInstanceRef.value?.formModel
}, (newData) => {
  if (!newData || !initialFormData.value || props.mode === 'view') {
    return
  }
  
  // 比较当前表单数据与初始数据是否一致
  try {
    const currentDataStr = JSON.stringify(newData)
    const initialDataStr = JSON.stringify(initialFormData.value)
    isFormModified.value = currentDataStr !== initialDataStr
  } catch {
    // 如果比较失败，不更新修改状态
  }
}, { deep: true, immediate: false })

// ==================== 方法 ====================
/**
 * 上传文件（参考 Dish.vue 的 uploadFile 函数）
 */
const uploadFile = async (file: FormData) => {
  try {
    const res = await fetch('/api/vadmin/system/upload/image/to/local', {
      method: 'POST',
      body: file,
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
      message: '上传成功',
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
 * 处理图片上传（参考 Dish.vue 的 handleImageUpload 函数）
 * 将图片字段中的数组格式（包含文件对象）转换为字符串格式（图片路径）
 */
const handleImageUpload = async (formData: any) => {
  // 遍历所有图片字段
  for (const field of props.formSchema) {
    if (field.type === 'image') {
      const imageField = field.field
      const imageDisplayField = `${field.field}_display`
      
      // 检查字段是否存在且为数组
      if (!formData[imageField] || !Array.isArray(formData[imageField])) {
        continue
      }
      
      // 处理每个图片项
      for (let index = 0; index < formData[imageField].length; index++) {
        const fileData = formData[imageField][index]
        
        // 如果是数组格式（包含文件对象），说明是未上传的图片，需要上传
        if (Array.isArray(fileData)) {
          const fileForm = new FormData()
          fileForm.append('file', fileData[3].raw)
          fileForm.append('path', 'system')
          const res = await uploadFile(fileForm)
          if (!res.success) {
            throw new Error(`图片上传错误：${res.message}`)
          }
          // 转换为字符串格式：路径 + 操作类型（add/update/delete）
          formData[imageField][index] = `${res.data.data.remote_path}?${fileData[1]}`
          formData[imageDisplayField][index] = `${res.data.data.remote_path}?${fileData[1]}`
        }
        // 如果已经是字符串格式，保持不变
        // 如果包含 ?delete 标记，保持原样（用于删除操作）
      }
    }
  }
}

/**
 * 处理保存
 */
const handleSave = async () => {
  // 等待表单注册完成
  if (!isFormRegistered.value) {
    // 等待多个 nextTick 确保表单已注册
    await nextTick()
    await nextTick()
  }
  
  const elForm = await getElFormExpose()
  if (!elForm) {
    ElMessage.error('表单未注册，请稍后重试')
    return
  }
  
  const valid = await elForm.validate()
  if (!valid) return

  let formData = await getFormData()
  
  // ==================== 处理图片字段上传 ====================
  // 如果存在未上传的图片，则处理上传
  try {
    await handleImageUpload(formData)
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '图片上传失败'
    ElMessage.error(errorMessage)
    return
  }
  
  // ==================== 扩展点3：提交前的数据处理钩子 ====================
  if (props.beforeSubmit) {
    try {
      formData = await props.beforeSubmit(formData) || formData
    } catch (error) {
      // 如果钩子抛出错误，停止提交
      return
    }
  }
  
  // 如果有提交接口，调用接口
  if (props.submitApi) {
    try {
      await props.submitApi(formData)
      ElMessage.success(props.mode === 'add' ? '新增成功' : '修改成功')
      // 保存成功后，重置修改标记
      isFormModified.value = false
      initialFormData.value = null
      emit('success')
      drawerVisible.value = false
    } catch (error) {
      // 提交失败时的错误处理由父组件或全局错误处理机制处理
    }
  } else {
    // 否则触发 save 事件，由父组件处理
    emit('save', formData)
  }
}

/**
 * 处理取消
 */
const handleCancel = () => {
  drawerVisible.value = false
  emit('cancel')
}

// ==================== 信息提示 ====================
/** 信息类型 */
type InfoType = 'info' | 'warn' | 'error'

/** 信息提示组件引用 */
const prompInfoRef = ref<InstanceType<typeof PrompInfo>>()

/**
 * 显示信息提示
 * @param type 信息类型：'info' | 'warn' | 'error'，为空时显示就绪状态
 * @param message 提示信息，为空时显示就绪状态
 */
const showInfo = (type?: InfoType | null, message?: string | null) => {
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

// ==================== 暴露方法 ====================
defineExpose({
  submit: handleSave,
  getFormData,
  setValues,
  getElFormExpose,
  showInfo // 显示信息提示
})
</script>

<template>
  <ElDrawer
    v-model="drawerVisible"
    :size="drawerWidth"
    direction="rtl"
    :close-on-click-modal="props.closeOnClickModal"
    :with-header="true"
    :title="drawerTitle"
    :before-close="handleBeforeClose"
    destroy-on-close
    class="base-free-drawer"
  >
    <!-- 表单内容区域（可滚动） -->
    <div class="base-free-content-wrapper">
      <ElScrollbar class="base-free-scrollbar">
        <div class="base-free-content">
          <div class="response-container">
            <!-- 按钮区域：提示信息 + 按钮 -->
            <!-- ==================== 扩展点6：按钮区域自定义 ==================== -->
            <slot name="buttons" :save="handleSave" :cancel="handleCancel" :mode="props.mode" :save-loading="props.saveLoading">
              <div class="response-buttons-wrapper">
                <div class="response-buttons-info">
                  <PrompInfo ref="prompInfoRef" />
                </div>
                <div class="response-buttons">
                  <ButtonPre
                    v-if="showSaveButton"
                    stype="save"
                    :loading="props.saveLoading"
                    @click="handleSave"
                  />
                  <ButtonPre
                    stype="return"
                    @click="handleCancel"
                  />
                </div>
              </div>
            </slot>
            
            <!-- Tab 组件 -->
            <ElTabs v-model="activeTab">
              <ElTabPane
                v-for="tab in filteredTabs"
                :key="tab.name"
                :label="tab.label"
                :name="tab.name"
              >
                <!-- ==================== 扩展点5：Tab 级别的自定义内容 ==================== -->
                <!-- 如果 Tab 配置了 customContent: true，使用插槽内容 -->
                <template v-if="tab.customContent">
                  <slot :name="`tab-${tab.name}`" :tab="tab" :current-row="props.currentRow" :mode="props.mode">
                    <!-- 默认插槽内容为空，由使用方提供 -->
                  </slot>
                </template>
                <!-- 基础信息 Tab：显示表单 -->
                <template v-else-if="tab.name !== 'log'">
                  <Form
                    :key="`form-${tab.name}-${drawerVisible}`"
                    :rules="props.rules"
                    :validate-on-rule-change="false"
                    @register="handleFormRegister"
                    :schema="getFieldsByTab(tab.name)"
                  />
                </template>
                <!-- 操作日志 Tab：显示占位内容 -->
                <template v-else>
                  <slot name="tab-log" :tab="tab" :current-row="props.currentRow" :mode="props.mode">
                    <div class="operation-log">
                      <p>操作日志功能待实现</p>
                    </div>
                  </slot>
                </template>
              </ElTabPane>
            </ElTabs>
          </div>
        </div>
      </ElScrollbar>
    </div>
  </ElDrawer>
</template>

<style lang="less">
:deep(.base-free-drawer) {
  .el-drawer {
    width: max(700px, calc(100vw - 600px)) !important;
    right: 0 !important;
    left: auto !important;
  }
}

:global(.base-free-drawer .el-drawer) {
  width: max(700px, calc(100vw - 600px)) !important;
  right: 0 !important;
  left: auto !important;
}

.base-free-content-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.base-free-scrollbar {
  flex: 1;
  min-height: 0;
  
  :deep(.el-scrollbar__wrap) {
    overflow-x: hidden;
  }
  
  .base-free-content {
    padding: 0 20px 20px 20px;
    max-width: 720px;
    margin-left: 0;
    margin-right: auto;
    
    :deep(.el-tabs) {
      padding: 0;
    }
    
    :deep(.el-tabs__header) {
      margin: 0;
      padding: 0;
    }
    
    :deep(.el-tabs__content) {
      padding: 0;
    }
  }
}

.response-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.response-buttons-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-top: 0;
  margin-bottom: 15px;
}

.response-buttons-info {
  flex: 1;
  min-width: 0;
}

.response-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  
  :deep(.my-button),
  :deep(.el-button) {
    margin: 0 !important;
  }
  
  > * {
    margin: 0 !important;
  }
}

.operation-log {
  padding: 20px;
  text-align: center;
  color: var(--el-text-color-secondary);
}

.base-free-drawer {
  :deep(.el-drawer__header) {
    margin-bottom: 0;
    padding: 15px 20px;
    border-bottom: 1px solid var(--el-border-color);
  }

  :deep(.el-drawer__body) {
    padding: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  :deep(.el-drawer__footer) {
    padding: 15px 20px;
    border-top: 1px solid var(--el-border-color);
  }
}

// 图片上传样式（与 Dish/components/Response.vue 保持一致）
.base-free-content {
  .image-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 0;
  }

  .image-container {
    .image-group {
      position: relative;
      width: 100px;
      height: 100px;
      margin: 0;
    }

    .image-item {
      width: 100%;
      height: 100%;
      border-radius: 6px;
      border: 1px solid #dcdfe6;
      transition: all 0.3s ease;
      cursor: pointer;
    }

    .image-item:hover {
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    // ElImage 组件样式
    .image-group :deep(.el-image) {
      width: 100%;
      height: 100%;
      border-radius: 6px;
    }

    .image-group :deep(.el-image__inner) {
      border-radius: 6px;
      object-fit: cover;
    }

    .remove-btn {
      position: absolute;
      top: -6px;
      right: -6px;
      width: 24px;
      height: 24px;
      background: #f56c6c;
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 12px;
      font-weight: bold;
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    .image-group:hover .remove-btn {
      opacity: 1;
    }

    .image-group.dragging {
      opacity: 0.5;
      border-color: #409eff;
      transform: scale(0.95);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
      cursor: grabbing;
      z-index: 1000;
    }

    .image-group.drag-over {
      transform: scale(1.15);
      border: 2px solid #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
      transform: scale(1.05);
      z-index: 10;
      transition: all 0.2s ease;
    }

    .image-group-uploader {
      width: 180px;
      height: 100px;
      flex-shrink: 0;
    }

    .image-group-uploader .el-upload {
      border: 2px dashed #c0c4cc;
      width: 100% !important;
      height: 96px !important;
      margin: 0 !important;
      border-radius: 6px;
    }

    .el-upload:hover {
      border-color: #409eff;
      background: #f0f7ff;
      color: #409eff;
    }

    .image-group-uploader .el-upload-dragger {
      width: 100% !important;
      height: 100% !important;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .el-icon--upload {
      width: 54px;
      height: 54px;
      margin-top: 0;
    }

    .upload-text {
      font-size: 12px;
      margin-top: -20px;
      text-align: center;
    }
  }
}
</style>

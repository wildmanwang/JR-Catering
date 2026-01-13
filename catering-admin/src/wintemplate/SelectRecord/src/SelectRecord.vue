<!--
  SelectRecord - 选择记录模板组件
  
  功能说明：
  这是一个通用的选择记录模板组件，用于在抽屉中展示可选择的记录列表。
  支持单选和多选模式，配置简单直接。
  
  主要功能：
  1. 查询条件：支持动态查询条件配置，查询参数默认值可在 searchSchema 中通过 value 属性设置
  2. 数据列表：支持分页、排序、高亮已选记录（仅多选模式）
  3. 选择功能：
     - 单选模式：点击记录后立即触发 select 事件并关闭窗口，不显示已选列表
     - 多选模式：点击记录切换选中状态，显示已选列表，支持拖拽排序，需要点击确认按钮触发 confirm 事件
  4. 已选列表：仅多选模式显示，支持拖拽排序
  5. 事件透传：支持 confirm、cancel、select 等事件
  
  配置方式：
  1. 查询条件配置：在使用端（如 SelectDish.vue、SelectDishgroup.vue）配置 searchSchema
  2. 列表字段配置：在使用端配置 tableColumns
  3. 数据源接口：在使用端配置 fetchDataApi
  4. 选择模式：通过 selectMode prop 设置（'single' | 'multiple'），默认为 'single'
  
  使用端配置示例：
  ```typescript
  // 查询条件配置（推荐在 searchSchema 中使用 value 属性设置默认值）
  const searchSchema = reactive<FormSchema[]>([
    {
      field: 'status',
      label: '状态',
      component: 'Select',
      value: 1, // 默认值
      componentProps: {
        placeholder: '请选择状态',
        ...
      }
    }
  ])
  
  // 表格列配置
  const tableColumns = reactive<TableColumn[]>([
    {
      field: 'name_unique',
      label: '名称',
      show: true,
      minWidth: '200px'
    }
  ])
  
  // 使用方式
  <SelectRecord
    v-model="drawerVisible"
    :search-schema="searchSchema"
    :fetch-data-api="getDishListApi"
    :table-columns="tableColumns"
    :row-key="'id'"
    :display-field="(row) => row.name_unique"
    :select-mode="'single'"
    @confirm="handleConfirm"
    @cancel="handleCancel"
    @select="handleSelect"
  />
  ```
  
  注意事项：
  1. 查询参数的默认值推荐在 searchSchema 中使用 value 属性设置，而不是使用 defaultSearchParams
  2. 单选模式：
     - 点击记录后立即触发 select 事件并关闭窗口
     - 不显示已选列表，不进行高亮处理
     - 不显示确认按钮（因为点击记录后直接返回）
  3. 多选模式：
     - 点击记录切换选中状态，已选记录会高亮显示
     - 显示已选列表，支持拖拽排序
     - 需要点击确认按钮才会触发 confirm 事件
  4. displayField 可以是字符串（字段名）或函数，用于在已选列表中显示记录（仅多选模式）
-->
<script setup lang="tsx">
import { computed, ref, watch, unref, nextTick } from 'vue'
import { ElScrollbar, ElCard, ElMenu, ElMenuItem, ElMessage } from 'element-plus'
import { ResponseDrawer, type ToolbarButton } from '@/wintemplate/ResponseDrawer'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { Table, TableColumn } from '@/components/Table'
import { useTable } from '@/hooks/web/useTable'
import { VueDraggable } from 'vue-draggable-plus'
import { ButtonPlus } from '@/components/ButtonPlus'
import { useSearch } from '@/hooks/web/useSearch'

defineOptions({
  name: 'SelectRecord'
})

// ==================== 类型定义 ====================
/** 选择模式 */
export type SelectMode = 'single' | 'multiple'

/** 组件 Props */
interface Props {
  modelValue: boolean // 抽屉显示状态
  title?: string // 抽屉标题
  width?: string | number // 抽屉宽度
  searchSchema?: FormSchema[] // 查询条件配置
  fetchDataApi?: (params: any) => Promise<any> // 数据源接口
  tableColumns?: TableColumn[] // 表格列配置
  rowKey?: string // 行唯一标识字段，默认 'id'
  displayField?: string | ((row: any) => string) // 显示字段或函数，用于已选列表显示
  defaultSearchParams?: Record<string, any> // 默认查询参数
  selectedRecords?: any[] // 初始已选记录
  maxSelect?: number // 最大选择数量，0表示不限制
  selectMode?: SelectMode // 选择模式，默认 'single'
  selectType?: 'row' | 'column' // 选择类型：'row' 表示选择行数据，'column' 表示选择列数据
}

// ==================== Props 定义 ====================
const props = withDefaults(defineProps<Props>(), {
  width: 'calc(100vw - 600px)',
  rowKey: 'id',
  selectedRecords: () => [],
  maxSelect: 0,
  selectMode: 'single', // 默认值：单选模式
  selectType: 'row'
})


// ==================== Emits 定义 ====================
// 注意：这些事件会自动透传到使用端，使用端可以直接监听，无需重复定义
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': [records: any[]] // 确认选择事件，返回已选记录列表
  'cancel': [] // 取消事件
  'select': [records: any[], type: 'row' | 'column'] // 选择事件，返回选中的记录和类型（行或列）
}>()

// ==================== 计算属性 ====================
/** 抽屉显示状态 */
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit('update:modelValue', val)
  }
})

/** 抽屉标题 */
const drawerTitle = computed(() => {
  return props.title || '选择记录'
})

/** 计算抽屉宽度 */
const drawerWidth = computed(() => {
  const defaultWidth = 'max(700px, calc(100vw - 600px))'
  if (props.width) {
    if (typeof props.width === 'string' && props.width !== defaultWidth) {
      return props.width
    }
    if (typeof props.width === 'number') {
      return props.width
    }
  }
  return defaultWidth
})

/** 计算工具栏按钮配置（用于传递给 ResponseDrawer） */
const toolbarButtons = computed<ToolbarButton[]>(() => {
  const buttons: ToolbarButton[] = []
  
  // 确认按钮（仅多选模式显示，单选模式下点击记录后直接返回，不需要确认按钮）
  if (selectMode.value === 'multiple') {
    buttons.push({
      stype: 'ok',
      show: true,
      onClick: handleConfirm
    })
  }
  
  return buttons
})


// ==================== 已选记录管理 ====================
/** 已选记录列表 */
const selectedList = ref<any[]>([])

/** 当前选中的已选记录索引 */
const activeSelectedIndex = ref<string>('')

/** 选择模式（使用端可设置，默认值为 'single'） */
const selectMode = computed<SelectMode>(() => {
  return props.selectMode || 'single'
})

/** 获取记录的显示文本 */
const getRecordDisplayText = (record: any): string => {
  if (typeof props.displayField === 'function') {
    return props.displayField(record)
  }
  if (typeof props.displayField === 'string') {
    return record[props.displayField] || String(record[props.rowKey || 'id'] || '')
  }
  // 默认使用 rowKey 或 id
  const key = props.rowKey || 'id'
  return String(record[key] || '')
}

/** 获取记录的唯一标识 */
const getRecordKey = (record: any): string | number => {
  const key = props.rowKey || 'id'
  return record[key]
}

/** 检查记录是否已选中 */
const isRecordSelected = (record: any): boolean => {
  const recordKey = getRecordKey(record)
  return selectedList.value.some(item => {
    const itemKey = getRecordKey(item)
    return itemKey === recordKey
  })
}

/**
 * 获取表格行的 class 名称（用于高亮已选中的记录）
 * 
 * 功能说明：
 * 1. 多选模式：检查当前行是否在已选列表中，如果在则返回高亮 class 名称
 * 2. 单选模式：不进行高亮处理（因为点击后直接返回，不需要高亮）
 * 3. 翻页时自动检查并高亮已选记录（仅多选模式）
 * 
 * 注意：Element Plus 的 row-class-name 函数接收的参数格式是 { row, rowIndex }
 * 但 Table 组件的 rowClassName prop 类型定义是 (row, rowIndex) => string
 * 所以这里需要适配两种调用方式
 * 
 * @param rowOrObj 当前行数据，或者包含 row 和 rowIndex 的对象
 * @returns class 名称字符串
 */
const getRowClassName = (rowOrObj: any): string => {
  // 单选模式下不进行高亮处理
  if (selectMode.value === 'single') {
    return ''
  }
  
  let row: any
  
  // 判断参数格式：如果是对象且包含 row 属性，说明是 Element Plus 的调用方式
  if (rowOrObj && typeof rowOrObj === 'object' && 'row' in rowOrObj) {
    row = rowOrObj.row
  } else {
    // 否则是 Table 组件的调用方式，第一个参数是 row
    row = rowOrObj
  }
  
  if (!row) {
    return ''
  }
  
  if (isRecordSelected(row)) {
    return 'selected-row-highlight'
  }
  return ''
}

/**
 * 表格更新 key（用于强制 Table 重新渲染，确保高亮状态正确）
 * 多选模式：当 selectedList 变化时，这个 key 会变化，从而触发 Table 重新渲染
 * 单选模式：不需要更新 key（因为不进行高亮处理）
 */
const tableUpdateKey = computed(() => {
  // 单选模式下不需要更新 key
  if (selectMode.value === 'single') {
    return 'single-mode'
  }
  
  // 多选模式：使用 selectedList 的长度和所有记录的 key 来生成 key
  // 这样当选中记录变化时，Table 会重新渲染，确保高亮状态正确
  const key = props.rowKey || 'id'
  const keys = selectedList.value.map(item => item[key]).sort().join(',')
  return `${selectedList.value.length}-${keys || 'empty'}`
})


/** 添加选中记录（仅多选模式使用） */
const addSelectedRecord = (record: any) => {
  // 单选模式下不应该调用此函数
  if (selectMode.value === 'single') {
    return
  }
  
  // 多选模式：检查是否已选中
  if (isRecordSelected(record)) {
    ElMessage.warning('该记录已选中')
    return
  }
  
  // 检查最大选择数量
  if (props.maxSelect > 0 && selectedList.value.length >= props.maxSelect) {
    ElMessage.warning(`最多只能选择 ${props.maxSelect} 条记录`)
    return
  }
  
  selectedList.value.push({ ...record })
  ElMessage.success('已添加到选择列表')
}

/**
 * 移除选中记录（通过索引，仅多选模式使用）
 * 
 * 功能说明：
 * 多选模式下，删除指定索引的记录
 */
const removeSelectedRecord = (index: number) => {
  // 单选模式下不应该调用此函数
  if (selectMode.value === 'single') {
    return
  }
  
  // 多选模式下，正常删除
  selectedList.value.splice(index, 1)
  if (activeSelectedIndex.value === String(index)) {
    activeSelectedIndex.value = ''
  }
}

/**
 * 移除选中记录（通过记录本身，仅多选模式使用）
 * @param record 要移除的记录
 */
const removeSelectedRecordByRecord = (record: any) => {
  // 单选模式下不应该调用此函数
  if (selectMode.value === 'single') {
    return
  }
  
  const recordKey = getRecordKey(record)
  const index = selectedList.value.findIndex(item => {
    const itemKey = getRecordKey(item)
    return itemKey === recordKey
  })
  
  if (index !== -1) {
    selectedList.value.splice(index, 1)
    if (activeSelectedIndex.value === String(index)) {
      activeSelectedIndex.value = ''
    }
    ElMessage.success('已取消选择')
  }
}

/**
 * 清空已选记录（仅多选模式使用）
 * 
 * 功能说明：
 * 1. 清空已选列表
 * 2. 清除选中效果（通过清空列表，getRowClassName 会自动移除高亮）
 * 3. 重置激活索引
 */
const clearSelectedRecords = () => {
  // 单选模式下不需要清空操作
  if (selectMode.value === 'single') {
    return
  }
  
  selectedList.value = []
  activeSelectedIndex.value = ''
}

/**
 * 选择指定记录（仅多选模式使用）
 * 
 * 功能说明：
 * 1. 将指定记录添加到已选列表
 * 2. 增加该行选中效果（通过添加到列表，getRowClassName 会自动添加高亮）
 * 
 * @param record 要选择的记录
 */
const selectRecord = (record: any) => {
  // 单选模式下不应该调用此函数
  if (selectMode.value === 'single') {
    return
  }
  
  selectedList.value.push({ ...record })
}

// 监听 props.selectedRecords 变化，初始化已选记录（仅多选模式）
watch(() => props.selectedRecords, (records) => {
  // 单选模式下不需要初始化已选记录
  if (selectMode.value === 'single') {
    return
  }
  
  if (records && records.length > 0) {
    selectedList.value = [...records]
  } else {
    selectedList.value = []
  }
}, { immediate: true, deep: true })


// ==================== 查询和表格 ====================
/** 查询参数 */
const searchParams = ref<Recordable>({})

/** 初始化默认查询参数 */
const initDefaultSearchParams = () => {
  searchParams.value = {}
  
  // 优先从 searchSchema 中提取默认值（推荐方式）
  if (props.searchSchema && props.searchSchema.length > 0) {
    props.searchSchema.forEach((item) => {
      // 如果字段有 value 属性且不为 undefined/null，则使用它作为默认值
      if (item.value !== undefined && item.value !== null) {
        searchParams.value[item.field] = item.value
      }
    })
  }
  
  // 兼容旧的方式：如果提供了 defaultSearchParams，则合并（优先级更高）
  if (props.defaultSearchParams) {
    searchParams.value = { ...searchParams.value, ...props.defaultSearchParams }
  }
}

/** 表格实例 */
const tableRef = ref<any>(null)

/**
 * 初始化表格
 * 
 * 功能说明：
 * 1. 从使用端（SelectDish.vue、SelectDishgroup.vue）接收 tableColumns 配置
 * 2. 创建表格实例
 * 3. 表格列配置直接传递给 Table 组件使用
 * 
 * 使用端配置示例：
 * ```typescript
 * const tableColumns = reactive<TableColumn[]>([
 *   {
 *     field: 'name_unique',
 *     label: '名称',
 *     show: true,
 *     minWidth: '200px'
 *   },
 *   {
 *     field: 'status',
 *     label: '状态',
 *     show: true,
 *     width: '100px',
 *     slots: {
 *       default: (data: any) => { ... }
 *     }
 *   }
 * ])
 * ```
 */
const initTable = () => {
  if (props.fetchDataApi && props.tableColumns) {
    // 确保查询参数已初始化
    initDefaultSearchParams()
    
    const { tableRegister, tableState, tableMethods } = useTable({
      immediate: false, // 不自动加载，手动控制加载时机
      fetchDataApi: async () => {
        const { pageSize, currentPage } = tableState
        // 每次调用时都获取最新的 searchParams（使用 unref 确保获取最新值）
        const currentSearchParams = unref(searchParams)
        const params = {
          page: unref(currentPage),
          limit: unref(pageSize),
          ...currentSearchParams
        }
        try {
          if (!props.fetchDataApi) {
            throw new Error('fetchDataApi 未定义')
          }
          // props.fetchDataApi 可能是一个返回 API 函数的函数，也可能直接是 API 函数
          // 先尝试调用它，如果返回的是函数，则使用返回的函数；否则直接使用它
          const apiFunc = typeof props.fetchDataApi === 'function' ? props.fetchDataApi() : props.fetchDataApi
          // 如果 apiFunc 还是函数，说明它是 API 函数本身，直接调用
          if (typeof apiFunc === 'function') {
            const res = await apiFunc(params)
            return {
              list: res.data || [],
              total: res.count || 0
            }
          } else {
            throw new Error('fetchDataApi 返回的不是函数')
          }
        } catch (error) {
          console.error('SelectRecord: fetchDataApi 调用失败:', error)
          throw error
        }
      }
    })
    
    tableRef.value = {
      register: tableRegister,
      state: tableState,
      methods: tableMethods
    }
  }
}

// 监听 fetchDataApi 和 tableColumns 变化，重新初始化表格
// 注意：不设置 immediate，只在 drawerVisible 为 true 时才初始化表格
watch([() => props.fetchDataApi, () => props.tableColumns], () => {
  // 只有在抽屉打开时才初始化表格
  if (drawerVisible.value) {
    initTable()
  }
})

// 监听 drawerVisible 变化，打开时初始化表格
watch(() => drawerVisible.value, async (val) => {
  if (val) {
    // 初始化已选记录（仅多选模式）
    if (selectMode.value === 'multiple') {
      if (props.selectedRecords && props.selectedRecords.length > 0) {
        selectedList.value = [...props.selectedRecords]
      } else {
        selectedList.value = []
      }
      activeSelectedIndex.value = ''
    }
    
    // 先初始化默认查询参数（确保在初始化表格前完成）
    initDefaultSearchParams()
    
    // 等待 Search 组件注册完成，并同步表单数据到 searchParams
    await nextTick()
    await nextTick()
    
    // 从 Search 组件获取表单数据（包含默认值）
    try {
      const formData = await searchMethods.getFormData()
      if (formData && typeof formData === 'object') {
        // 合并表单数据和默认查询参数（表单数据优先级更高）
        searchParams.value = { ...searchParams.value, ...formData }
      }
    } catch (error) {
      // Search 组件可能还未注册，使用默认查询参数
    }
    
    // 窗口打开时，确保表格已初始化（在 searchParams 初始化之后）
    if (!tableRef.value) {
      initTable()
    }
    
    // 刷新表格
    await nextTick()
    if (tableRef.value?.methods?.getList) {
      await tableRef.value.methods.getList()
    }
  } else {
    // 关闭时清空已选记录（仅多选模式）
    if (selectMode.value === 'multiple') {
      selectedList.value = []
      activeSelectedIndex.value = ''
    }
  }
})

/** Search 组件引用和 hook */
const { searchRegister, searchMethods } = useSearch()

/**
 * 处理查询条件的 schema
 * 
 * 功能说明：
 * 1. 从使用端（SelectDish.vue、SelectDishgroup.vue）接收 searchSchema 配置
 * 2. 隐藏所有字段的 label（设置为空字符串，labelWidth 为 0）
 * 3. 宽度处理规则：
 *    - 如果使用端在 componentProps.style.width 中配置了宽度，优先使用配置的宽度
 *    - Select 组件（下拉组件）默认宽度为 200px（如果未配置）
 *    - Input 组件（输入框）设置为 flex: 1，填充剩余空间
 * 
 * 使用端配置示例：
 * ```typescript
 * const searchSchema = reactive<FormSchema[]>([
 *   {
 *     field: 'status',
 *     label: '状态',
 *     component: 'Select',
 *     componentProps: {
 *       placeholder: '请选择状态',
 *       style: {
 *         width: '150px' // 可在使用端配置宽度
 *       }
 *     }
 *   },
 *   {
 *     field: 'fuzzy_query_str',
 *     label: '模糊查询',
 *     component: 'Input',
 *     componentProps: {
 *       placeholder: '请输入名称',
 *       style: {
 *         width: '300px' // 可在使用端配置宽度，如果不配置则 flex: 1
 *       }
 *     }
 *   }
 * ])
 * ```
 */
const processedSearchSchema = computed(() => {
  if (!props.searchSchema || props.searchSchema.length === 0) {
    return []
  }
  
  // 解析并处理每个查询字段
  return props.searchSchema.map(field => {
    const processedField: FormSchema = {
      ...field,
      label: '', // 隐藏 label
      formItemProps: {
        ...field.formItemProps,
        labelWidth: '0px' // 设置 labelWidth 为 0
      }
    }
    
    // 处理组件宽度
    const componentType = field.component || ''
    const existingStyle = (field.componentProps as any)?.style || {}
    const hasCustomWidth = existingStyle.width !== undefined
    
    // 构建新的样式对象
    const newStyle: Record<string, any> = { ...existingStyle }
    
    if (componentType === 'Input') {
      // Input 组件（模糊查询）：无论是否配置宽度，都设置为 flex 填充剩余空间
      // 移除固定宽度配置，使用 flex 布局
      delete newStyle.width
      newStyle.width = '100%' // 组件本身宽度 100%，由 form-item 的 flex 控制填充
    } else if (componentType === 'Select') {
      // Select 组件：如果使用端没有配置宽度，默认宽度 200px
      if (!hasCustomWidth) {
        newStyle.width = '200px'
      }
      // 如果使用端配置了宽度，保留配置的宽度
    }
    
    // 更新 componentProps
    processedField.componentProps = {
      ...field.componentProps,
      style: newStyle
    }
    
    // 为 Input 组件的 form-item 添加 class，用于 CSS 选择器（总是添加，确保 flex 填充）
    if (componentType === 'Input') {
      const existingClass = processedField.formItemProps?.class || ''
      const classArray = Array.isArray(existingClass) ? existingClass : existingClass ? [existingClass] : []
      processedField.formItemProps = {
        ...processedField.formItemProps,
        class: [...classArray, 'search-form-item-input']
      }
    }
    
    // 为 Select 组件的 form-item 添加 class，用于 CSS 选择器
    // 同时直接在 form-item 上设置宽度，确保小宽度能够生效
    if (componentType === 'Select') {
      const existingClass = processedField.formItemProps?.class || ''
      const classArray = Array.isArray(existingClass) ? existingClass : existingClass ? [existingClass] : []
      const selectWidth = newStyle.width || '200px'
      processedField.formItemProps = {
        ...processedField.formItemProps,
        class: [...classArray, 'search-form-item-select'],
        style: {
          ...processedField.formItemProps?.style,
          width: selectWidth, // 直接在 form-item 上设置宽度
          maxWidth: selectWidth, // 同时设置最大宽度，防止被拉伸
          flexShrink: '0' // 防止被 flex 布局压缩
        }
      }
    }
    
    return processedField
  })
})

/** 处理查询 */
const handleSearch = async (params?: Recordable) => {
  if (params) {
    searchParams.value = { ...params }
  } else {
    // 如果没有传入参数，从 Search 组件获取表单数据
    try {
      const formData = await searchMethods.getFormData()
      if (formData) {
        // 过滤空值（但保留空字符串，因为模糊查询可能需要空字符串）
        const filteredData = Object.keys(formData).reduce((prev, next) => {
          const value = formData[next]
          // 只过滤 null 和 undefined，保留空字符串（fuzzy_query_str 可能为空字符串）
          if (value !== null && value !== undefined) {
            prev[next] = value
          }
          return prev
        }, {} as Recordable)
        searchParams.value = { ...filteredData }
      }
    } catch (error) {
      // 如果获取失败，使用当前的 searchParams
    }
  }
  // 等待 Vue 响应式系统更新 searchParams
  await nextTick()
  // 刷新表格
  if (tableRef.value?.methods?.getList) {
    await tableRef.value.methods.getList()
  }
}

/** 处理查询按钮点击 */
const handleQueryClick = () => {
  handleSearch()
}


// ==================== 方法 ====================
/** 处理确认（仅多选模式使用） */
const handleConfirm = () => {
  // 单选模式下不应该调用此函数（因为单选模式下点击记录后直接返回）
  if (selectMode.value === 'single') {
    return
  }
  
  const records = [...selectedList.value]
  emit('confirm', records)
  drawerVisible.value = false
}

/** 处理取消 */
const handleCancel = () => {
  drawerVisible.value = false
  emit('cancel')
}

/** 处理表格行选择 */
/**
 * 处理表格行点击事件
 * 
 * 功能说明：
 * 1. 单选模式：
 *    - 点击记录后立即触发 select 事件并关闭窗口
 *    - 不维护已选列表，不进行高亮处理
 * 2. 多选模式：
 *    - 如果记录已选中，则取消选中（从已选列表中移除）
 *    - 如果记录未选中，则添加到已选列表
 *    - 已选中的记录会高亮显示
 */
const handleTableRowClick = (row: any) => {
  if (selectMode.value === 'single') {
    // 单选模式：直接触发 select 事件并关闭窗口
    // 不需要维护已选列表，不需要高亮处理
    emit('select', [{ ...row }], props.selectType)
    drawerVisible.value = false
  } else {
    // 多选模式：切换选中状态
    const isSelected = isRecordSelected(row)
    if (isSelected) {
      // 如果已选中，则取消选中
      removeSelectedRecordByRecord(row)
    } else {
      // 如果未选中，则添加到已选列表
      // 检查最大选择数量
      if (props.maxSelect > 0 && selectedList.value.length >= props.maxSelect) {
        ElMessage.warning(`最多只能选择 ${props.maxSelect} 条记录`)
        return
      }
      selectRecord(row)
      ElMessage.success('已添加到选择列表')
    }
  }
}


/** 处理已选记录拖拽结束 */
const handleDragEnd = () => {
  // 拖拽结束后可以在这里处理排序逻辑
}

// ==================== ResponseDrawer 引用 ====================
const responseDrawerRef = ref<InstanceType<typeof ResponseDrawer>>()

// ==================== 暴露方法 ====================
defineExpose({
  getSelectedRecords: () => {
    // 单选模式下返回空数组（因为不维护已选列表）
    if (selectMode.value === 'single') {
      return []
    }
    return [...selectedList.value]
  },
  clearSelectedRecords
})
</script>

<template>
  <ResponseDrawer
    ref="responseDrawerRef"
    v-model="drawerVisible"
    :title="drawerTitle"
    :width="drawerWidth"
    :toolbar-buttons="toolbarButtons"
    @close="handleCancel"
    @cancel="handleCancel"
  >
    <!-- 
      工具栏左侧：查询条件和查询按钮
      说明：
      - props.searchSchema: 从使用端（SelectDish.vue、SelectDishgroup.vue）传递的查询条件配置
      - processedSearchSchema: 模板中解析处理后的查询条件（隐藏 label，特殊处理状态字段宽度）
    -->
    <template #toolbar-left>
      <div v-if="props.searchSchema && props.searchSchema.length > 0" class="search-toolbar-inline">
        <div class="search-form-wrapper">
          <Search
            :schema="processedSearchSchema"
            :show-search="false"
            :show-reset="false"
            :label-width="0"
            :is-col="false"
            :inline="true"
            @register="searchRegister"
          />
        </div>
        <div class="query-button-wrapper">
          <ButtonPlus stype="query" @click="handleQueryClick" />
        </div>
      </div>
    </template>

    <!-- 主体内容区域 -->
    <div class="select-record-content">
      <!-- 左侧：已选记录（仅多选模式显示） -->
      <div v-if="selectMode === 'multiple'" class="selected-records-panel">
        <ElCard class="selected-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>已选列表</span>
              <span class="selected-count">({{ selectedList.length }})</span>
            </div>
          </template>
          <ElScrollbar class="selected-scrollbar">
            <VueDraggable
              v-model="selectedList"
              :animation="200"
              handle=".drag-handle"
              @end="handleDragEnd"
            >
              <ElMenu
                v-model:default-active="activeSelectedIndex"
                class="selected-menu"
              >
                <ElMenuItem
                  v-for="(record, index) in selectedList"
                  :key="index"
                  :index="String(index)"
                  class="selected-menu-item"
                >
                  <div class="menu-item-content">
                    <span class="drag-handle">☰</span>
                    <span class="menu-item-text">
                      {{ getRecordDisplayText(record) }}
                    </span>
                    <span
                      class="menu-item-remove"
                      @click.stop="removeSelectedRecord(index)"
                    >
                      ✕
                    </span>
                  </div>
                </ElMenuItem>
              </ElMenu>
            </VueDraggable>
            <div v-if="selectedList.length === 0" class="empty-selected">
              暂无已选记录
            </div>
          </ElScrollbar>
        </ElCard>
      </div>

      <!-- 右侧：选择区 -->
      <div :class="['select-panel', { 'select-panel-full': selectMode === 'single' }]">
        <div class="table-content">
          <!-- 
            查询列表区
            说明：
            - props.tableColumns: 从使用端（SelectDish.vue、SelectDishgroup.vue）传递的表格列配置
            - props.fetchDataApi: 从使用端传递的数据获取接口
            - 模板直接使用这些配置，无需额外解析
          -->
          <div v-if="props.fetchDataApi && props.tableColumns" class="table-area">
            <Table
              v-if="tableRef"
              :key="`table-${tableUpdateKey}`"
              :columns="props.tableColumns"
              :data="tableRef.state.dataList"
              :loading="tableRef.state.loading"
              :pagination="{
                total: tableRef.state.total
              }"
              v-model:current-page="tableRef.state.currentPage"
              v-model:page-size="tableRef.state.pageSize"
              :highlight-current-row="false"
              :row-class-name="(params: any) => getRowClassName(params)"
              :row-key="props.rowKey || 'id'"
              @register="tableRef.register"
              @row-click="(row: any) => handleTableRowClick(row)"
            />
          </div>
        </div>
      </div>
    </div>
  </ResponseDrawer>
</template>

<style lang="less" scoped>
/* SelectRecord 内容区样式 */
.select-record-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  gap: 10px; /* 已选列表与备选列表间隔 10px */
}

.selected-records-panel {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .selected-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    :deep(.el-card__body) {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      padding: 0;
    }

    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;

      .selected-count {
        color: var(--el-color-primary);
        font-weight: normal;
      }
    }
  }

  .selected-scrollbar {
    flex: 1;
    min-height: 0;

    :deep(.el-scrollbar__wrap) {
      overflow-x: hidden;
    }
  }

  .selected-menu {
    border: none;
    width: 100%;

    .selected-menu-item {
      padding: 0;
      height: auto;
      line-height: normal;

      .menu-item-content {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 15px;
        width: 100%;

        .drag-handle {
          cursor: move;
          color: var(--el-text-color-secondary);
          font-size: 14px;
          user-select: none;
        }

        .menu-item-text {
          flex: 1;
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .menu-item-remove {
          cursor: pointer;
          color: var(--el-color-danger);
          font-size: 16px;
          padding: 0 4px;
          opacity: 0.7;
          transition: opacity 0.2s;

          &:hover {
            opacity: 1;
          }
        }
      }

      &:hover {
        background-color: var(--el-fill-color-light);
      }
    }
  }

  .empty-selected {
    padding: 40px 20px;
    text-align: center;
    color: var(--el-text-color-placeholder);
  }
}

/* 备选列表：左对齐，填满右侧空间 */
.select-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  /* 单选模式下，表格占满整个宽度 */
  &.select-panel-full {
    flex: 1;
  }

  .table-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .table-area {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
}

/* 高亮已选中的行：蓝底白字 */
:deep(.el-table) {
  .selected-row-highlight {
    --el-table-tr-bg-color: var(--el-color-primary);
    background-color: var(--el-color-primary) !important;
    color: #ffffff !important;
    
    /* 单元格文字颜色 */
    td {
      color: #ffffff !important;
      background-color: var(--el-color-primary) !important;
    }
    
    /* hover 时稍微变深 */
    &:hover {
      --el-table-tr-bg-color: var(--el-color-primary-dark-2);
      background-color: var(--el-color-primary-dark-2) !important;
      
      td {
        background-color: var(--el-color-primary-dark-2) !important;
      }
    }
  }
}

/* 工具栏左侧的查询组件样式 */
.search-toolbar-inline {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding-left: 20px;

  /* 查询表单包装器，flex填充剩余空间 */
  .search-form-wrapper {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: center;
  }

  /* 查询按钮包装器，右对齐 */
  .query-button-wrapper {
    flex-shrink: 0;
    display: flex;
    align-items: center;
  }

  /* 隐藏查询条件的所有 label */
  :deep(.el-form-item__label) {
    display: none !important;
    width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  /* 查询条件横向布局，多个条件显示为一行，间隔10px */
  :deep(.el-form) {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: nowrap;
    width: 100%;
  }

  :deep(.el-form-item) {
    margin-bottom: 0;
    margin-right: 0;
  }
  
  /* Input 组件的 form-item 设置为 flex 填充剩余空间 */
  :deep(.el-form-item.search-form-item-input) {
    flex: 1;
    min-width: 0;
  }
  
  /* Select 组件的 form-item 保持固定宽度，不收缩 */
  /* 宽度通过内联样式设置，这里只确保不被压缩 */
  :deep(.el-form-item.search-form-item-select) {
    flex-shrink: 0 !important;
    min-width: 0 !important; /* 允许宽度小于默认值，覆盖 Element Plus 的默认最小宽度 */
  }
  
  /* Select 组件的 form-item content 区域也设置宽度，确保小宽度生效 */
  :deep(.el-form-item.search-form-item-select .el-form-item__content) {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important; /* 允许宽度小于默认值，覆盖 Element Plus 的默认最小宽度 */
  }
  
  /* 覆盖 inline 布局中的默认最小宽度 */
  :deep(.el-form--inline .el-form-item.search-form-item-select .el-form-item__content > :first-child) {
    min-width: 0 !important; /* 覆盖 Element Plus inline 布局的默认最小宽度 229.5px */
  }
  
  /* 确保 Input 组件本身宽度 100% */
  :deep(.el-input) {
    width: 100%;
  }
  
  /* Select 组件在 form-item 内占满 form-item 的宽度 */
  :deep(.el-form-item.search-form-item-select .el-select) {
    width: 100%;
    max-width: 100%;
  }
  
  /* Select 组件内部的 wrapper 元素也要设置宽度和最大宽度，确保小宽度生效 */
  :deep(.el-form-item.search-form-item-select .el-select__wrapper) {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box;
  }
}
</style>


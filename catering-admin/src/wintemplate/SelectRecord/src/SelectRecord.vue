<!--
  SelectRecord - 选择记录模板组件
  
  功能说明：
  这是一个通用的选择记录模板组件，用于在抽屉中展示可选择的记录列表。
  
  配置方式：
  1. 查询条件配置：在使用端（如 SelectDish.vue、SelectDishgroup.vue）配置 searchSchema
  2. 列表字段配置：在使用端配置 tableColumns
  3. 模板解析：在 SelectRecord.vue 中解析这些配置并渲染
  
  使用端配置示例：
  ```typescript
  // 查询条件配置
  const searchSchema = reactive<FormSchema[]>([
    {
      field: 'status',
      label: '状态',
      component: 'Select',
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
  
  // Tab 配置
  const tabs = ref<SelectTab[]>([
    {
      label: '选择菜品',
      name: 'select',
      searchSchema: searchSchema,
      fetchDataApi: getDishListApi,
      tableColumns: tableColumns,
      ...
    }
  ])
  ```
  
  模板解析逻辑：
  1. processedSearchSchema: 解析查询条件，隐藏 label，特殊处理状态字段宽度为 120px
  2. tab.tableColumns: 直接传递给 Table 组件使用，无需额外解析
-->
<script setup lang="tsx">
import { computed, ref, watch, unref, nextTick } from 'vue'
import { ElScrollbar, ElTabs, ElTabPane, ElCard, ElMenu, ElMenuItem, ElMessage } from 'element-plus'
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

/** Tab 配置 */
export interface SelectTab {
  label: string // Tab 标签
  name: string // Tab 名称
  searchSchema?: FormSchema[] // 查询条件配置
  fetchDataApi?: (params: any) => Promise<any> // 数据源接口
  tableColumns?: TableColumn[] // 表格列配置
  rowKey?: string // 行唯一标识字段，默认 'id'
  displayField?: string | ((row: any) => string) // 显示字段或函数，用于已选列表显示
  defaultSearchParams?: Record<string, any> // 默认查询参数
  selectMode?: SelectMode // 选择模式：'single' | 'multiple'，默认 'multiple'
}

/** 组件 Props */
interface Props {
  modelValue: boolean // 抽屉显示状态
  title?: string // 抽屉标题
  width?: string | number // 抽屉宽度
  tabs?: SelectTab[] // Tab 配置，默认1个选项卡
  selectedRecords?: any[] // 初始已选记录
  maxSelect?: number // 最大选择数量，0表示不限制
  selectMode?: SelectMode // 全局选择模式，如果 Tab 中没有配置则使用此值
  selectType?: 'row' | 'column' // 选择类型：'row' 表示选择行数据，'column' 表示选择列数据
}

// ==================== Props 定义 ====================
const props = withDefaults(defineProps<Props>(), {
  width: 'calc(100vw - 600px)',
  tabs: () => [
    { label: '选择', name: 'select' }
  ],
  selectedRecords: () => [],
  maxSelect: 0,
  selectMode: undefined, // 不设置默认值，由 getSelectMode 函数处理默认值逻辑
  selectType: 'row'
})


// ==================== Emits 定义 ====================
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
  
  // 确认按钮
  buttons.push({
    stype: 'ok',
    show: true,
    onClick: handleConfirm
  })
  
  return buttons
})

// ==================== Tab 管理 ====================
const activeTab = ref(props.tabs[0]?.name || 'select')

// 监听 tabs 变化，确保 activeTab 始终有效
watch(() => props.tabs, (tabs) => {
  if (tabs.length > 0) {
    const currentTabExists = tabs.find(tab => tab.name === activeTab.value)
    if (!currentTabExists) {
      activeTab.value = tabs[0].name
    }
  }
}, { immediate: true })

// 监听 activeTab 变化，初始化默认查询参数并刷新数据
watch(() => activeTab.value, () => {
  initDefaultSearchParams()
  // 刷新当前 Tab 的表格
  const currentTable = tableRefs.value[activeTab.value]
  if (currentTable?.methods?.getList) {
    currentTable.methods.getList()
  }
})

// ==================== 已选记录管理 ====================
/** 已选记录列表 */
const selectedList = ref<any[]>([])

/** 当前选中的已选记录索引 */
const activeSelectedIndex = ref<string>('')

/** 获取记录的显示文本 */
const getRecordDisplayText = (record: any, tab: SelectTab): string => {
  if (typeof tab.displayField === 'function') {
    return tab.displayField(record)
  }
  if (typeof tab.displayField === 'string') {
    return record[tab.displayField] || String(record[tab.rowKey || 'id'] || '')
  }
  // 默认使用 rowKey 或 id
  const key = tab.rowKey || 'id'
  return String(record[key] || '')
}

/** 获取记录的唯一标识 */
const getRecordKey = (record: any, tab: SelectTab): string | number => {
  const key = tab.rowKey || 'id'
  return record[key]
}

/** 检查记录是否已选中 */
const isRecordSelected = (record: any, tab: SelectTab): boolean => {
  const recordKey = getRecordKey(record, tab)
  return selectedList.value.some(item => {
    const itemKey = getRecordKey(item, tab)
    return itemKey === recordKey
  })
}

/**
 * 获取表格行的 class 名称（用于高亮已选中的记录）
 * 
 * 功能说明：
 * 1. 检查当前行是否在已选列表中
 * 2. 如果在已选列表中，返回高亮 class 名称
 * 3. 支持单选和多选模式
 * 4. 翻页时自动检查并高亮已选记录
 * 
 * 注意：Element Plus 的 row-class-name 函数接收的参数格式是 { row, rowIndex }
 * 但 Table 组件的 rowClassName prop 类型定义是 (row, rowIndex) => string
 * 所以这里需要适配两种调用方式
 * 
 * @param rowOrObj 当前行数据，或者包含 row 和 rowIndex 的对象
 * @param tab Tab 配置（可选，如果第一个参数是对象则第二个参数是 tab）
 * @returns class 名称字符串
 */
const getRowClassName = (rowOrObj: any, tab?: SelectTab): string => {
  let row: any
  let targetTab: SelectTab | undefined = tab
  
  // 判断参数格式：如果是对象且包含 row 属性，说明是 Element Plus 的调用方式
  if (rowOrObj && typeof rowOrObj === 'object' && 'row' in rowOrObj) {
    row = rowOrObj.row
    // 如果没有传入 tab，使用当前激活的 tab
    if (!targetTab) {
      targetTab = currentTab.value
    }
  } else {
    // 否则是 Table 组件的调用方式，第一个参数是 row，第二个参数是 tab
    row = rowOrObj
    targetTab = tab || currentTab.value
  }
  
  if (!targetTab || !row) {
    return ''
  }
  
  if (isRecordSelected(row, targetTab)) {
    return 'selected-row-highlight'
  }
  return ''
}

/**
 * 表格更新 key（用于强制 Table 重新渲染，确保高亮状态正确）
 * 当 selectedList 变化时，这个 key 会变化，从而触发 Table 重新渲染
 * 这样可以确保翻页时已选记录也能正确高亮显示
 */
const tableUpdateKey = computed(() => {
  // 使用 selectedList 的长度和所有记录的 key 来生成 key
  // 这样当选中记录变化时，Table 会重新渲染，确保高亮状态正确
  const tab = currentTab.value
  const key = tab.rowKey || 'id'
  const keys = selectedList.value.map(item => item[key]).sort().join(',')
  return `${selectedList.value.length}-${keys || 'empty'}`
})

/**
 * 获取当前 Tab 的选择模式
 * 
 * 优先级：
 * 1. tab.selectMode（Tab 配置中的选择模式）
 * 2. props.selectMode（组件 props 中的选择模式）
 * 3. 'single'（默认值：如果使用方没有配置，则使用单选模式）
 */
const getSelectMode = (tab: SelectTab): SelectMode => {
  return tab.selectMode || props.selectMode || 'single'
}

/** 添加选中记录 */
const addSelectedRecord = (record: any, tab: SelectTab) => {
  const selectMode = getSelectMode(tab)
  
  // 单选模式：如果已选中其他记录，先清空
  if (selectMode === 'single') {
    if (selectedList.value.length > 0) {
      selectedList.value = []
    }
  } else {
    // 多选模式：检查是否已选中
    if (isRecordSelected(record, tab)) {
      ElMessage.warning('该记录已选中')
      return
    }
    
    // 检查最大选择数量
    if (props.maxSelect > 0 && selectedList.value.length >= props.maxSelect) {
      ElMessage.warning(`最多只能选择 ${props.maxSelect} 条记录`)
      return
    }
  }
  
  selectedList.value.push({ ...record })
  if (selectMode === 'single') {
    ElMessage.success('已选择')
  } else {
    ElMessage.success('已添加到选择列表')
  }
}

/**
 * 移除选中记录（通过索引）
 * 
 * 功能说明：
 * 1. 单选模式下，删除记录后清空已选列表
 * 2. 多选模式下，正常删除指定索引的记录
 */
const removeSelectedRecord = (index: number) => {
  const tab = currentTab.value
  const selectMode = getSelectMode(tab)
  
  if (selectMode === 'single') {
    // 单选模式下，删除记录后清空已选列表
    selectedList.value = []
    activeSelectedIndex.value = ''
  } else {
    // 多选模式下，正常删除
    selectedList.value.splice(index, 1)
    if (activeSelectedIndex.value === String(index)) {
      activeSelectedIndex.value = ''
    }
  }
}

/**
 * 移除选中记录（通过记录本身）
 * @param record 要移除的记录
 * @param tab Tab 配置
 */
const removeSelectedRecordByRecord = (record: any, tab: SelectTab) => {
  const recordKey = getRecordKey(record, tab)
  const index = selectedList.value.findIndex(item => {
    const itemKey = getRecordKey(item, tab)
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
 * 清空已选记录
 * 
 * 功能说明：
 * 1. 清空已选列表
 * 2. 清除选中效果（通过清空列表，getRowClassName 会自动移除高亮）
 * 3. 重置激活索引
 */
const clearSelectedRecords = () => {
  selectedList.value = []
  activeSelectedIndex.value = ''
}

/**
 * 选择指定记录
 * 
 * 功能说明：
 * 1. 将指定记录添加到已选列表
 * 2. 增加该行选中效果（通过添加到列表，getRowClassName 会自动添加高亮）
 * 
 * @param record 要选择的记录
 */
const selectRecord = (record: any) => {
  selectedList.value.push({ ...record })
}

// 监听 props.selectedRecords 变化，初始化已选记录
watch(() => props.selectedRecords, (records) => {
  if (records && records.length > 0) {
    selectedList.value = [...records]
  } else {
    selectedList.value = []
  }
}, { immediate: true, deep: true })


// ==================== 查询和表格 ====================
/** 当前激活的 Tab */
const currentTab = computed(() => {
  return props.tabs.find(tab => tab.name === activeTab.value) || props.tabs[0]
})

/** 查询参数 */
const searchParams = ref<Recordable>({})

/** 初始化默认查询参数 */
const initDefaultSearchParams = () => {
  const tab = currentTab.value
  if (tab.defaultSearchParams) {
    searchParams.value = { ...tab.defaultSearchParams }
  } else {
    searchParams.value = {}
  }
}

/** 表格实例映射（Tab名称 -> 表格实例） */
const tableRefs = ref<Record<string, any>>({})

/**
 * 初始化表格（为每个 Tab 创建表格实例）
 * 
 * 功能说明：
 * 1. 从使用端（SelectDish.vue、SelectDishgroup.vue）接收 tableColumns 配置
 * 2. 为每个 Tab 创建独立的表格实例
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
const initTables = () => {
  props.tabs.forEach(tab => {
    if (tab.fetchDataApi && tab.tableColumns) {
      const { tableRegister, tableState, tableMethods } = useTable({
        fetchDataApi: async () => {
          const { pageSize, currentPage } = tableState
          const res = await tab.fetchDataApi!({
            page: unref(currentPage),
            limit: unref(pageSize),
            ...unref(searchParams)
          })
          return {
            list: res.data || [],
            total: res.count || 0
          }
        }
      })
      
      tableRefs.value[tab.name] = {
        register: tableRegister,
        state: tableState,
        methods: tableMethods
      }
    }
  })
}

// 监听 tabs 变化，重新初始化表格
watch(() => props.tabs, () => {
  initTables()
}, { immediate: true, deep: true })

// 监听 drawerVisible 变化，打开时初始化表格
watch(() => drawerVisible.value, (val) => {
  if (val) {
    // 窗口打开时，确保表格已初始化
    if (Object.keys(tableRefs.value).length === 0) {
      initTables()
    }
    // 初始化已选记录
    if (props.selectedRecords && props.selectedRecords.length > 0) {
      selectedList.value = [...props.selectedRecords]
    } else {
      selectedList.value = []
    }
    activeSelectedIndex.value = ''
    // 初始化默认查询参数
    initDefaultSearchParams()
    // 刷新当前 Tab 的表格
    nextTick(() => {
      const currentTable = tableRefs.value[activeTab.value]
      if (currentTable?.methods?.getList) {
        currentTable.methods.getList()
      }
    })
  } else {
    // 关闭时清空已选记录
    selectedList.value = []
    activeSelectedIndex.value = ''
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
  const tab = currentTab.value
  if (!tab.searchSchema || tab.searchSchema.length === 0) {
    return []
  }
  
  // 解析并处理每个查询字段
  return tab.searchSchema.map(field => {
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
    const formData = await searchMethods.getFormData()
    // 过滤空值
    const filteredData = Object.keys(formData).reduce((prev, next) => {
      const value = formData[next]
      if (value !== null && value !== undefined && value !== '') {
        prev[next] = value
      }
      return prev
    }, {} as Recordable)
    searchParams.value = { ...filteredData }
  }
  // 刷新当前 Tab 的表格
  const currentTable = tableRefs.value[activeTab.value]
  if (currentTable?.methods?.getList) {
    currentTable.methods.getList()
  }
}

/** 处理查询按钮点击 */
const handleQueryClick = () => {
  handleSearch()
}


// ==================== 方法 ====================
/** 处理确认 */
const handleConfirm = () => {
  emit('confirm', [...selectedList.value])
  drawerVisible.value = false
}

/** 处理选择（用于直接返回数据给调用方，不关闭窗口） */
const handleSelect = (type: 'row' | 'column') => {
  if (selectedList.value.length > 0) {
    emit('select', [...selectedList.value], type)
    // 单选模式下，选择后自动关闭窗口
    const tab = currentTab.value
    if (getSelectMode(tab) === 'single') {
      drawerVisible.value = false
    } else {
      // 多选模式下，清空已选列表，继续选择
      selectedList.value = []
    }
  }
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
 *    - 如果该记录已经是选中状态，则不变、返回
 *    - 如果该记录未选中，则执行清除已选记录、选择当前点击记录
 *    - 选择后立即触发 select 事件并关闭窗口
 * 2. 多选模式：
 *    - 如果记录已选中，则取消选中（从已选列表中移除）
 *    - 如果记录未选中，则添加到已选列表
 *    - 已选中的记录会高亮显示
 */
const handleTableRowClick = (row: any, tab: SelectTab) => {
  const selectMode = getSelectMode(tab)
  const isSelected = isRecordSelected(row, tab)
  
  if (selectMode === 'single') {
    // 单选模式：如果该记录已经是选中状态，则不变、返回
    if (isSelected) {
      return
    }
    
    // 如果该记录未选中，则执行清除已选记录、选择当前点击记录
    clearSelectedRecords()
    selectRecord(row)
    
    // 单选模式下，选择后立即触发 select 事件并关闭窗口
    emit('select', [{ ...row }], props.selectType)
    drawerVisible.value = false
  } else {
    // 多选模式：切换选中状态
    if (isSelected) {
      // 如果已选中，则取消选中
      removeSelectedRecordByRecord(row, tab)
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
  getSelectedRecords: () => [...selectedList.value],
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
      - currentTab.searchSchema: 从使用端（SelectDish.vue、SelectDishgroup.vue）传递的查询条件配置
      - processedSearchSchema: 模板中解析处理后的查询条件（隐藏 label，特殊处理状态字段宽度）
    -->
    <template #toolbar-left>
      <div v-if="currentTab.searchSchema && currentTab.searchSchema.length > 0" class="search-toolbar-inline">
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
      <!-- 左侧：已选记录 -->
      <div class="selected-records-panel">
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
              :disabled="getSelectMode(currentTab) === 'single'"
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
                    <span v-if="getSelectMode(currentTab) === 'multiple'" class="drag-handle">☰</span>
                    <span class="menu-item-text">
                      {{ getRecordDisplayText(record, currentTab) }}
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
      <div class="select-panel">
        <ElTabs v-model="activeTab" class="select-tabs">
          <ElTabPane
            v-for="tab in props.tabs"
            :key="tab.name"
            :label="tab.label"
            :name="tab.name"
          >
            <div class="tab-content">
              <!-- 
                查询列表区
                说明：
                - tab.tableColumns: 从使用端（SelectDish.vue、SelectDishgroup.vue）传递的表格列配置
                - tab.fetchDataApi: 从使用端传递的数据获取接口
                - 模板直接使用这些配置，无需额外解析
              -->
              <div v-if="tab.fetchDataApi && tab.tableColumns" class="table-area">
                <Table
                  v-if="tableRefs[tab.name]"
                  :key="`table-${tab.name}-${tableUpdateKey}`"
                  :columns="tab.tableColumns"
                  :data="tableRefs[tab.name].state.dataList"
                  :loading="tableRefs[tab.name].state.loading"
                  :pagination="{
                    total: tableRefs[tab.name].state.total
                  }"
                  v-model:current-page="tableRefs[tab.name].state.currentPage"
                  v-model:page-size="tableRefs[tab.name].state.pageSize"
                  :highlight-current-row="false"
                  :row-class-name="(params: any) => getRowClassName(params, tab)"
                  :row-key="tab.rowKey || 'id'"
                  @register="tableRefs[tab.name].register"
                  @row-click="(row: any) => handleTableRowClick(row, tab)"
                />
              </div>
            </div>
          </ElTabPane>
        </ElTabs>
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

/* 备选列表：含 tabPane 组件，左对齐，填满右侧空间 */
.select-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .select-tabs {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    :deep(.el-tabs__content) {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    :deep(.el-tab-pane) {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
  }

  .tab-content {
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


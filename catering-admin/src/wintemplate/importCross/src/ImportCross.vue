<!--
  ImportCross - 交叉数据导入模板
  
  功能：
  - 处理行数据和列数据的交叉数据配置
  - 支持多套配置值切换
  - 根据配置自动显示选择按钮
  - 支持从源窗口自动读取数据
-->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick, toRaw } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { WinSheet, type StatusStoreItem } from '@/wintemplate/WinSheet'
import TableCross, { type TableCrossRow, type TableCrossColumn, type TableCrossDataConfigs } from '@/components/TableCross/src/TableCross.vue'
import { ButtonPlus } from '@/components/ButtonPlus'
import { PromptInfo } from '@/components/PromptInfo'
import { ElSelect, ElOption, ElRadioGroup, ElRadioButton } from 'element-plus'
import { getBranchListApi } from '@/api/vadmin/system/branch'

/**
 * 行数据配置
 */
export interface RowDataConfig {
  /** 数据名称，例如：菜品 */
  name: string
  /** 是否支持新增行 */
  allowAdd: boolean
}

/**
 * 列数据配置
 */
export interface ColDataConfig {
  /** 数据名称，例如：菜品分组 */
  name: string
  /** 是否支持新增列 */
  allowAdd: boolean
}

/**
 * 组件 Props 接口
 */
/**
 * 组件 Props 接口
 */
export interface ImportCrossProps {
  /** 数据存储的 sessionStorage key（用于在页面间传递数据） */
  storageKey?: string
  /** 源数据存储的 sessionStorage key（用于从上一个窗口自动读取数据，如 ImportBase） */
  sourceStorageKey?: string
  /** @deprecated 使用 rowDatas 代替 */
  dishes?: any[]
  /** @deprecated 使用 colDatas 代替 */
  dishGroups?: any[]
  /** 行数据配置 */
  rowDataConfig?: RowDataConfig
  /** 列数据配置 */
  colDataConfig?: ColDataConfig
  /** 窗口标识 */
  windowId?: string
  /** 名称列宽度（第一列） */
  nameColumnWidth?: number
  /** 数据列宽度 */
  dataColumnWidth?: number
  /** 汇总列宽度 */
  sumColumnWidth?: number
  /** 数据配置数组（支持多套数据配置） */
  dataConfigs?: TableCrossDataConfigs
  /** 保存处理函数 */
  onSave?: (data: any) => Promise<void> | void
}

const props = withDefaults(defineProps<ImportCrossProps>(), {
  storageKey: 'IMPORT_CROSS_PAYLOAD',
  sourceStorageKey: '',
  dishes: () => [],
  dishGroups: () => [],
  rowDataConfig: () => ({ name: '行数据', allowAdd: true }),
  colDataConfig: () => ({ name: '列数据', allowAdd: true }),
  windowId: 'ImportCross',
  nameColumnWidth: 200,
  dataColumnWidth: 160,
  sumColumnWidth: 120,
  dataConfigs: () => []
})

const emit = defineEmits<{
  (e: 'dataChanged', data: any): void
  (e: 'save', data: any): void
  (e: 'select-row-data'): void // 选择行数据事件
  (e: 'select-col-data'): void // 选择列数据事件
}>()

// ==================== 状态管理 ====================
/** 门店ID */
const branchId = ref<number | null>(null)

/** 门店选项列表 */
const branchOptions = ref<any[]>([])

/** 数据切换类型：'use_dish' | 'price_add'（向后兼容，当没有数据配置时使用） */
const dataType = ref<'use_dish' | 'price_add'>('use_dish')

/** 当前选中的数据配置索引（从0开始） */
const currentDataConfigIndex = ref<number>(0)

/** Dish记录列表 */
const dishList = ref<any[]>([])

/** DishGroup记录列表 */
const dishGroupList = ref<any[]>([])

/** 交叉数据配置（多套配置值） */
const crossData = ref<{
  use_dish: Record<string, Record<string, number | null>> // { dishId: { dishGroupId: value } }
  price_add: Record<string, Record<string, number | null>> // { dishId: { dishGroupId: value } }
}>({
  use_dish: {},
  price_add: {}
})

// ==================== 组件引用 ====================
const prompInfoRef = ref<InstanceType<typeof PromptInfo>>()
const tableCrossRef = ref<InstanceType<typeof TableCross>>()
const winSheetRef = ref<InstanceType<typeof WinSheet>>()

// 为了在模板中使用
const dataConfigs = computed(() => props.dataConfigs ?? [])
const nameColumnWidth = computed(() => props.nameColumnWidth)
const dataColumnWidth = computed(() => props.dataColumnWidth)
const sumColumnWidth = computed(() => props.sumColumnWidth)
const rowDataConfig = computed(() => props.rowDataConfig)
const colDataConfig = computed(() => props.colDataConfig)

// ==================== 计算属性 ====================
/** TableCross的行数据（Dish） */
const tableRows = computed<TableCrossRow[]>(() => {
  return dishList.value.map(dish => {
    const row: TableCrossRow = {
      id: dish.id,
      name: dish.name_unique || ''
    }
    
    // 为每个DishGroup列添加所有数据配置的值
    dishGroupList.value.forEach(group => {
      // 如果有数据配置，使用多套数据存储
      if (props.dataConfigs && props.dataConfigs.length > 0) {
        props.dataConfigs.forEach((config, configIndex) => {
          const dataKey = `__data_${configIndex}_${group.id}`
          // 从 crossData 中获取值（保持向后兼容）
          const oldValue = crossData.value[dataType.value]?.[String(dish.id)]?.[String(group.id)]
          // 优先使用新格式，如果没有则使用旧格式
          row[dataKey] = oldValue ?? null
        })
      } else {
        // 没有数据配置，使用旧的格式（向后兼容）
        const value = crossData.value[dataType.value]?.[String(dish.id)]?.[String(group.id)] ?? null
        row[String(group.id)] = value
      }
    })
    
    // 操作列由 TableCross 组件单独处理，不需要在这里添加数据
    
    return row
  })
})

/** TableCross的列数据（DishGroup） */
const tableColumns = computed<TableCrossColumn[]>(() => {
  // 先创建数据列（不包括操作列）
  const columns = dishGroupList.value.map(group => ({
    id: group.id,
    name: group.name_unique || ''
  }))
  
  // 操作列会在 TableCross 组件中单独添加，放在行小计之后
  // 这里不添加操作列，让 TableCross 组件处理
  
  return columns
})

// ==================== 初始化 ====================
/**
 * 加载门店列表
 */
const loadBranchList = async () => {
  try {
    const res = await getBranchListApi({ is_active: true })
    if (res?.data) {
      branchOptions.value = Array.isArray(res.data) ? res.data : []
    }
  } catch (error) {
    if (prompInfoRef.value) {
      prompInfoRef.value.err('加载门店列表失败')
    }
  }
}

/**
 * 从源窗口（如 ImportBase）加载数据
 */
const loadDataFromSource = () => {
  if (!props.sourceStorageKey) return
  
  try {
    const sourceData = sessionStorage.getItem(props.sourceStorageKey)
    if (sourceData) {
      const parsed = JSON.parse(sourceData)
      
      // ImportGrid 存储的数据格式：
      // 1. { action: 'import', data: [...] } - ImportGrid 自动保存的格式
      // 2. { data: [...] } - 从 BaseGrid 传入的格式
      // 3. 直接是数组格式
      let sourceList: any[] = []
      if (Array.isArray(parsed)) {
        sourceList = parsed
      } else if (parsed && typeof parsed === 'object') {
        if (parsed.action === 'import' && Array.isArray(parsed.data)) {
          // 格式1：ImportGrid 自动保存的格式
          sourceList = parsed.data
        } else if (Array.isArray(parsed.data)) {
          // 格式2：对象格式，包含 data
          sourceList = parsed.data
        }
      }
      
      // 将源窗口的数据作为 DishGroup（列）显示
      if (sourceList.length > 0) {
        dishGroupList.value = sourceList.map(item => ({
          id: item.id,
          name_unique: item.name_unique || item.name_display || '',
          ...item // 保留原始数据
        }))
        
        if (prompInfoRef.value) {
          prompInfoRef.value.info(`已从上一个窗口加载 ${dishGroupList.value.length} 个分组`)
        }
      } else {
        // 数据为空，提示用户
        if (prompInfoRef.value) {
          prompInfoRef.value.warn('上一个窗口没有数据')
        }
      }
    } else {
      // 没有找到数据
      if (prompInfoRef.value) {
        prompInfoRef.value.warn('未找到上一个窗口的数据，请先在 ImportBase 中添加数据')
      }
    }
  } catch (error) {
    if (prompInfoRef.value) {
      prompInfoRef.value.err('从上一个窗口加载数据失败')
    }
  }
}

/**
 * 从sessionStorage加载数据
 * @param shouldRestore - 是否应该恢复缓存（窗口切换时为 true，窗口打开时为 false）
 */
const loadDataFromStorage = (shouldRestore: boolean = false) => {
  if (!props.storageKey) {
    return
  }
  
  // 窗口打开场景：清空缓存，不恢复
  if (!shouldRestore) {
    try {
      sessionStorage.removeItem(props.storageKey)
    } catch (error) {
      // 静默处理
    }
    // 清空后直接返回，不加载数据
    return
  }
  
  // 窗口切换或页面刷新场景：恢复缓存
  try {
    const storageData = sessionStorage.getItem(props.storageKey)
    
    if (storageData) {
      const data = JSON.parse(storageData)
      
      // 加载Dish和DishGroup数据
      // 注意：如果 props 中有数据，优先使用 props（但页面刷新时 props 通常是空的）
      if (data.dishes && Array.isArray(data.dishes)) {
        // 只有在 props 中没有数据时才使用缓存的数据
        if (!props.dishes || props.dishes.length === 0) {
          dishList.value = data.dishes
        }
      }
      if (data.dishGroups && Array.isArray(data.dishGroups)) {
        // 只有在 props 中没有数据时才使用缓存的数据
        if (!props.dishGroups || props.dishGroups.length === 0) {
          dishGroupList.value = data.dishGroups
        }
      }
      if (data.branchId !== undefined) {
        branchId.value = data.branchId
      }
      if (data.crossData) {
        crossData.value = data.crossData
      }
    }
  } catch (error) {
    // 加载数据失败，静默处理
  }
  
  // 如果props中有数据，优先使用props（覆盖缓存数据）
  if (props.dishes && props.dishes.length > 0) {
    dishList.value = props.dishes
  }
  if (props.dishGroups && props.dishGroups.length > 0) {
    dishGroupList.value = props.dishGroups
  }
}

/**
 * 保存数据到sessionStorage
 */
const saveDataToStorage = () => {
  if (!props.storageKey) {
    return
  }
  
  try {
    const data = {
      dishes: dishList.value,
      dishGroups: dishGroupList.value,
      branchId: branchId.value,
      crossData: crossData.value
    }
    sessionStorage.setItem(props.storageKey, JSON.stringify(data))
  } catch (error) {
    // 保存数据失败，静默处理
  }
}

// ==================== 事件处理 ====================
/**
 * 处理单元格更新
 */
const handleCellUpdate = (rowIndex: number, columnIndex: number, value: number | null, dataConfigIndex?: number) => {
  const row = tableRows.value[rowIndex]
  const column = tableColumns.value[columnIndex]
  
  if (!row || !column) return
  
  const dishId = String(row.id)
  const dishGroupId = String(column.id)
  const configIndex = dataConfigIndex ?? currentDataConfigIndex.value
  
  // 如果有数据配置，使用多套数据存储
  if (props.dataConfigs && props.dataConfigs.length > 0) {
    // 初始化数据结构（保持向后兼容）
    if (!crossData.value[dataType.value][dishId]) {
      crossData.value[dataType.value][dishId] = {}
    }
    
    // 更新值（保持向后兼容）
    crossData.value[dataType.value][dishId][dishGroupId] = value
  } else {
    // 没有数据配置，使用旧的格式
    if (!crossData.value[dataType.value][dishId]) {
      crossData.value[dataType.value][dishId] = {}
    }
    crossData.value[dataType.value][dishId][dishGroupId] = value
  }
  
  // 保存到storage
  saveDataToStorage()
  
  // 触发事件
  emit('dataChanged', {
    dishId: row.id,
    dishGroupId: column.id,
    dataType: dataType.value,
    dataConfigIndex: configIndex,
    value
  })
}

/**
 * 处理行数据更新
 */
const handleRowsUpdate = (rows: TableCrossRow[]) => {
  // 更新 dishList 的顺序以匹配新的行顺序
  // rows 中的顺序就是新的顺序
  const newDishList: any[] = []
  rows.forEach(row => {
    // 查找对应的 dish
    const dish = dishList.value.find(d => d.id === row.id)
    if (dish) {
      newDishList.push(dish)
    }
  })
  
  // 更新 dishList 的顺序
  dishList.value = newDishList
  
  // 更新交叉数据
  rows.forEach(row => {
    const dishId = String(row.id)
    dishGroupList.value.forEach(group => {
      const groupId = String(group.id)
      const value = row[groupId] ?? null
      
      if (!crossData.value[dataType.value][dishId]) {
        crossData.value[dataType.value][dishId] = {}
      }
      crossData.value[dataType.value][dishId][groupId] = value
    })
  })
  
  saveDataToStorage()
}

/**
 * 处理列数据更新
 */
const handleColumnsUpdate = (columns: TableCrossColumn[]) => {
  // 列更新时，需要重新构建交叉数据
  dishGroupList.value = columns.map(col => {
    const existing = dishGroupList.value.find(g => g.id === col.id)
    return existing || { id: col.id, name_unique: col.name }
  })
  
  saveDataToStorage()
}

/**
 * 新增行数据（菜品）
 * @param records - 要添加的行数据记录列表
 */
const addRowDatas = (records: any[]) => {
  if (!records || records.length === 0) return
  
  // 过滤掉已存在的记录
  const newRecords = records.filter(record => {
    const recordId = record.id
    return !dishList.value.some(item => item.id === recordId)
  })
  
  if (newRecords.length > 0) {
    dishList.value.push(...newRecords)
    saveDataToStorage()
    if (prompInfoRef.value) {
      prompInfoRef.value.info(`已添加 ${newRecords.length} 条行数据`)
    }
  } else {
    if (prompInfoRef.value) {
      prompInfoRef.value.warn('所选记录已存在')
    }
  }
}

/**
 * 新增列数据（分组）
 * @param records - 要添加的列数据记录列表
 */
const addColDatas = (records: any[]) => {
  if (!records || records.length === 0) return
  
  // 过滤掉已存在的记录
  const newRecords = records.filter(record => {
    const recordId = record.id
    return !dishGroupList.value.some(item => item.id === recordId)
  })
  
  if (newRecords.length > 0) {
    dishGroupList.value.push(...newRecords)
    saveDataToStorage()
    if (prompInfoRef.value) {
      prompInfoRef.value.info(`已添加 ${newRecords.length} 条列数据`)
    }
  } else {
    if (prompInfoRef.value) {
      prompInfoRef.value.warn('所选记录已存在')
    }
  }
}

/**
 * 删除行数据（菜品）
 * @param rowIndex - 要删除的行索引（来自 TableCross，是 tableData 中的索引）
 */
const deleteRow = (rowIndex: number) => {
  // rowIndex 是 tableData 中的索引
  // tableData 的结构：数据行 + 汇总行 + 操作行（如果启用）
  // 所以如果 rowIndex >= dishList.length，说明是汇总行或操作行，不处理
  if (rowIndex < 0 || rowIndex >= dishList.value.length) {
    return
  }
  
  const dish = dishList.value[rowIndex]
  const dishId = String(dish.id)
  
  // 删除行数据
  dishList.value.splice(rowIndex, 1)
  
  // 删除交叉数据中该行的所有数据
  if (crossData.value[dataType.value][dishId]) {
    delete crossData.value[dataType.value][dishId]
  }
  
  saveDataToStorage()
  
  if (prompInfoRef.value) {
    prompInfoRef.value.info('已删除行数据')
  }
  
  // 触发数据变化事件
  emit('dataChanged', {
    action: 'delete-row',
    dishId: dish.id
  })
}

/**
 * 删除列数据（分组）
 * @param columnIndex - 要删除的列索引（来自 TableCross，可能包括操作列）
 */
const deleteColumn = (columnIndex: number) => {
  // 获取当前列（可能包括操作列）
  const column = tableColumns.value[columnIndex]
  
  // 如果是操作列，不处理
  if (!column || String(column.id) === '__action_column__') {
    return
  }
  
  // 查找该列在 dishGroupList 中的实际索引
  const actualIndex = dishGroupList.value.findIndex(group => group.id === column.id)
  
  if (actualIndex < 0 || actualIndex >= dishGroupList.value.length) return
  
  const group = dishGroupList.value[actualIndex]
  const groupId = String(group.id)
  
  // 删除列数据
  dishGroupList.value.splice(actualIndex, 1)
  
  // 删除交叉数据中该列的所有数据
  Object.keys(crossData.value[dataType.value]).forEach(dishId => {
    if (crossData.value[dataType.value][dishId] && crossData.value[dataType.value][dishId][groupId]) {
      delete crossData.value[dataType.value][dishId][groupId]
    }
  })
  
  saveDataToStorage()
  
  if (prompInfoRef.value) {
    prompInfoRef.value.info('已删除列数据')
  }
  
  // 触发数据变化事件
  emit('dataChanged', {
    action: 'delete-column',
    dishGroupId: group.id
  })
}

/**
 * 选择列数据（分组）
 * 触发 select-col-data 事件，通知父组件打开列数据选择窗口
 */
const handleSelectGroup = () => {
  emit('select-col-data')
}

/**
 * 选择行数据（菜品）
 * 触发 select-row-data 事件，通知父组件打开行数据选择窗口
 */
const handleSelectDish = () => {
  emit('select-row-data')
}

/**
 * 保存数据
 * 如果配置了 onSave 函数，则调用它；否则触发 save 事件
 */
const handleSave = async () => {
  if (prompInfoRef.value) {
    prompInfoRef.value.info('正在保存...')
  }
  
  // 保存到storage
  saveDataToStorage()
  
  // 构建保存数据
  const saveData = {
    branchId: branchId.value,
    dishes: dishList.value,
    dishGroups: dishGroupList.value,
    crossData: crossData.value
  }
  
  // 如果配置了保存处理函数，调用它
  if (props.onSave) {
    try {
      await props.onSave(saveData)
      if (prompInfoRef.value) {
        prompInfoRef.value.info('保存成功')
      }
    } catch (error) {
      if (prompInfoRef.value) {
        prompInfoRef.value.err('保存失败')
      }
    }
  } else {
    // 触发保存事件
    emit('save', saveData)
    if (prompInfoRef.value) {
      prompInfoRef.value.info('保存成功')
    }
  }
}

// ==================== 监听 ====================
/** 监听数据类型切换，更新表格数据 */
watch(dataType, () => {
  // 数据类型切换时，表格会自动通过computed更新
  if (prompInfoRef.value) {
    prompInfoRef.value.info(`已切换到${dataType.value === 'use_dish' ? '使用菜品' : '配置加价'}`)
  }
})

/** 监听数据配置索引切换 */
watch(currentDataConfigIndex, (newIndex) => {
  if (prompInfoRef.value && props.dataConfigs && props.dataConfigs[newIndex]) {
    prompInfoRef.value.info(`已切换到${props.dataConfigs[newIndex].label}`)
  }
})

/** 初始化：如果有数据配置，默认选中第一个 */
watch(() => props.dataConfigs, (configs) => {
  if (configs && configs.length > 0 && currentDataConfigIndex.value >= configs.length) {
    currentDataConfigIndex.value = 0
  }
}, { immediate: true })

// ==================== 状态存储配置（用于 WinSheet） ====================
/**
 * 配置状态存储（用于 WinSheet 的 StatusStoragePlus）
 */
const stateStores = computed<StatusStoreItem[]>(() => {
  const stores: StatusStoreItem[] = [
    {
      name: 'importCross',
      getState: () => {
        return {
          branchId: branchId.value,
          currentDataConfigIndex: currentDataConfigIndex.value,
          dataType: dataType.value
        }
      },
      setState: async (state: any) => {
        if (state.branchId !== undefined) {
          branchId.value = state.branchId
        }
        if (state.currentDataConfigIndex !== undefined) {
          currentDataConfigIndex.value = state.currentDataConfigIndex
        }
        if (state.dataType) {
          dataType.value = state.dataType
        }
      }
    }
  ]
  return stores
})

/**
 * 状态恢复完成回调
 */
const handleRestoreComplete = async (restored: boolean) => {
  if (restored) {
    // 状态已恢复，可以加载 sessionStorage 中的数据（窗口切换或页面刷新场景）
    loadDataFromStorage(true)
  } else {
    // 窗口打开场景：检查是否是页面刷新
    // 页面刷新时，sessionStorage 中的数据应该还在，应该恢复
    // 只有在真正的新窗口打开时（sessionStorage 中没有数据），才清空缓存
    if (props.storageKey) {
      const storageData = sessionStorage.getItem(props.storageKey)
      if (storageData) {
        // 有缓存数据，说明是页面刷新场景，应该恢复
        loadDataFromStorage(true)
      } else {
        // 没有缓存数据，说明是真正的窗口打开场景，清空缓存
        loadDataFromStorage(false)
      }
    } else {
      // 没有配置 storageKey，直接清空
      loadDataFromStorage(false)
    }
  }
}

// ==================== 监听源窗口数据变化 ====================
/**
 * 使用 StorageEvent 监听 sessionStorage 变化（跨标签页）
 * 注意：同源页面的 sessionStorage 变化不会触发 StorageEvent
 * 所以这里使用 focus 事件作为补充
 */
const handleStorageChange = (event: StorageEvent) => {
  if (event.key === props.sourceStorageKey && event.newValue) {
    loadDataFromSource()
    saveDataToStorage()
  }
}

const handleWindowFocus = () => {
  // 窗口获得焦点时，重新加载源数据（确保数据是最新的）
  if (props.sourceStorageKey) {
    loadDataFromSource()
    saveDataToStorage()
  }
}

/**
 * 路由守卫：离开页面前保存 sessionStorage 数据
 * 注意：状态缓存由 WinSheet 的 StatusStoragePlus 自动处理
 */
onBeforeRouteLeave((_to, _from, next) => {
  // 保存数据到 sessionStorage（用于窗口间传递数据）
  if (props.storageKey) {
    saveDataToStorage()
  }
  next()
})

// ==================== 生命周期 ====================
onMounted(async () => {
  await loadBranchList()
  
  // 先加载源窗口数据（如果配置了）
  if (props.sourceStorageKey) {
    loadDataFromSource()
    
    // 监听 sessionStorage 变化（跨标签页）
    window.addEventListener('storage', handleStorageChange)
    // 监听窗口焦点变化（同标签页内切换回来时）
    window.addEventListener('focus', handleWindowFocus)
  }
  
  // 等待 WinSheet 的状态恢复完成
  // WinSheet 会在状态恢复完成后调用 handleRestoreComplete
  // 在 handleRestoreComplete 中根据 restored 参数决定是否加载 sessionStorage 数据
  
  if (prompInfoRef.value) {
    prompInfoRef.value.info('就绪')
  }
})

// 组件卸载时清理
onBeforeUnmount(() => {
  if (props.sourceStorageKey) {
    window.removeEventListener('storage', handleStorageChange)
    window.removeEventListener('focus', handleWindowFocus)
  }
  
  // 窗口关闭时的 sessionStorage 清理由 WinSheet 的 StatusStoragePlus 自动处理
  // 这里只需要清理事件监听器
})

// ==================== 暴露方法 ====================
defineExpose({
  getData: () => ({
    branchId: branchId.value,
    dishes: dishList.value,
    dishGroups: dishGroupList.value,
    crossData: crossData.value
  }),
  saveDataToStorage,
  addRowDatas,
  addColDatas,
  getRowDatas: () => [...dishList.value],
  getColDatas: () => [...dishGroupList.value]
})
</script>

<template>
  <WinSheet
    ref="winSheetRef"
    :window-id="props.windowId || 'ImportCross'"
    :stores="stateStores"
    :storage-prefix="props.windowId ? `${props.windowId}_STATE_` : 'IMPORT_CROSS_STATE_'"
    :on-restore-complete="handleRestoreComplete"
  >
    <div class="import-cross-container">
    <!-- 顶部工具栏 -->
    <div class="import-cross-toolbar">
      <div class="toolbar-left">
        <!-- 门店下拉选择 -->
        <ElSelect
          v-model="branchId"
          placeholder="请选择门店"
          style="width: 160px"
          clearable
          @change="saveDataToStorage"
        >
          <ElOption
            v-for="branch in branchOptions"
            :key="branch.id"
            :label="branch.name_unique"
            :value="branch.id"
          />
        </ElSelect>
        
        <!-- 数据切换组件：只有当数据配置数组存在且长度 > 1 时才显示 -->
        <ElRadioGroup 
          v-if="dataConfigs && dataConfigs.length > 1"
          :model-value="currentDataConfigIndex"
          @update:model-value="(val: number) => { currentDataConfigIndex = val }"
          class="data-type-switch"
        >
          <ElRadioButton
            v-for="(config, index) in dataConfigs"
            :key="index"
            :label="index"
          >{{ config.label }}</ElRadioButton>
        </ElRadioGroup>
      </div>
      
      <!-- PromptInfo组件 -->
      <div class="toolbar-info">
        <PromptInfo ref="prompInfoRef" />
      </div>
      
      <!-- 右侧按钮组 -->
      <div class="toolbar-right">
        <!-- 根据配置显示按钮 -->
        <template v-if="rowDataConfig?.allowAdd">
          <ButtonPlus
            stype="select"
            @click="handleSelectDish"
          >
            {{ rowDataConfig.name }}
          </ButtonPlus>
        </template>
        <template v-if="colDataConfig?.allowAdd">
          <ButtonPlus
            stype="select"
            @click="handleSelectGroup"
          >
            {{ colDataConfig.name }}
          </ButtonPlus>
        </template>
        <!-- 如果没有配置，显示默认按钮（向后兼容） -->
        <template v-if="!rowDataConfig && !colDataConfig">
          <ButtonPlus
            stype="select"
            @click="handleSelectGroup"
          >分组</ButtonPlus>
          <ButtonPlus
            stype="select"
            @click="handleSelectDish"
          >菜品</ButtonPlus>
        </template>
        <ButtonPlus
          stype="save"
          @click="handleSave"
        />
      </div>
    </div>
    
    <!-- TableCross组件 -->
    <div class="table-wrapper">
      <TableCross
        ref="tableCrossRef"
        :rows="tableRows"
        :columns="tableColumns"
        :name-column-width="nameColumnWidth"
        :data-column-width="dataColumnWidth"
        :sum-column-width="sumColumnWidth"
        :data-configs="dataConfigs"
        :current-data-config-index="currentDataConfigIndex"
        :allow-delete-row="rowDataConfig?.allowAdd || false"
        :allow-delete-column="colDataConfig?.allowAdd || false"
        @update:rows="handleRowsUpdate"
        @update:columns="handleColumnsUpdate"
        @cell-update="handleCellUpdate"
        @update:current-data-config-index="(val: number) => { currentDataConfigIndex = val }"
        @row-delete="deleteRow"
        @column-delete="deleteColumn"
      />
    </div>
  </div>
  </WinSheet>
</template>

<style lang="less" scoped>
.import-cross-container {
  padding: 0 !important;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.import-cross-toolbar {
  display: flex;
  align-items: center;
  margin: 0 0 10px 0;
  gap: 10px;
  flex-shrink: 0;
}

.toolbar-left {
  flex: 0 0 auto;
  display: flex;
  gap: 10px;
  align-items: center;
}

.toolbar-info {
  flex: 1;
  min-width: 0;
}

.toolbar-right {
  flex: 0 0 auto;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

// 确保在 ContentWrap 容器中正确显示
// 这些样式确保 ImportCross 能够填充整个 ContentWrap 容器的高度
// 与 ImportGrid 保持完全一致的样式
:deep(.content-wrap),
:deep(.content-wrap .el-card),
:deep(.content-wrap .el-card__body) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
  margin: 0 !important;
}

:deep(.content-wrap .el-card__body) {
  flex: 1 !important;
  min-height: 0 !important;
  overflow: hidden !important;
  padding: 0 !important;
}

:deep(.content-wrap > div) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  padding: 0 !important;
  margin: 0 !important;
}
</style>


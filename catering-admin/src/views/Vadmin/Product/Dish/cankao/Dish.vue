<script setup lang="tsx">
import { reactive, ref, unref, toRaw, onMounted, watch, onBeforeUnmount, nextTick } from 'vue'
import {
  getDishListApi,
  addDishListApi,
  delDishListApi,
  putDishListApi,
  getDishApi
} from '@/api/vadmin/product/dish'
import { getDishCategoryWithCountApi } from '@/api/vadmin/product/dishcategory'
import { getBranchOptionsApi } from '@/api/vadmin/basicinfo/branch'
import { getDishStatusOptionsApi } from '@/api/vadmin/basicinfo/basicdict'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { useTable } from '@/hooks/web/useTable'
import { Table, TableColumn } from '@/components/Table'
    import { ButtonPlus } from '@/components/ButtonPlus'
import { ElRow, ElCol, ElImage, ElMenu, ElMenuItem, ElCard, ElMessage } from 'element-plus'
import { Dialog } from '@/components/Dialog'
import Write from './components/Write.vue'
import { BaseButton } from '@/components/Button'
import { useRouter } from 'vue-router'

defineOptions({
  name: 'ProductDish'
})

const { push } = useRouter()

const categories = ref([])
const activeIndex = ref(0)
const curCategory = ref(null)
const fetchCategories = async () => {
  const res = await getDishCategoryWithCountApi()
  if (!res?.data) {
    categories.value = []
    return
  }
  categories.value = res.data
}
fetchCategories()

const search = ref(null)
const searchRegistered = ref(false)
const pendingSearchParams = ref<any>(null)

// 监听Search组件的register事件
const handleSearchRegister = async () => {
  searchRegistered.value = true
  
  // 如果有待恢复的表单显示值，立即设置
  if (pendingSearchParams.value && search.value && typeof search.value.setValues === 'function') {
    await nextTick()
    await nextTick()
    try {
      await search.value.setValues(pendingSearchParams.value)
      lastSearchParams.value = { ...pendingSearchParams.value }
      pendingSearchParams.value = null
    } catch (err) {
      console.error('恢复Search组件值失败：', err)
    }
  }
}
const handleSelect = (index) => {
  const selected = categories.value.find(c => c.id.toString() === index)
  if (selected) {
    activeIndex.value = index
    if (index > '0') {
      curCategory.value = parseInt(index)
    } else {
      curCategory.value = null
    }
  } else {
    curCategory.value = null
  }
  // 更新查询条件，包含菜品分类
  const categoryId = curCategory.value
  searchParams.value = {...searchParams.value, dish_category_id: categoryId}
  // 同时更新lastSearchParams（表单显示值）
  if (!lastSearchParams.value) {
    lastSearchParams.value = {}
  }
  if (categoryId !== null && categoryId !== undefined) {
    lastSearchParams.value.dish_category_id = categoryId
  } else {
    delete lastSearchParams.value.dish_category_id
  }
  // 保存状态并执行查询
  savePageState()
  getList()
}

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const { pageSize, currentPage } = tableState
    const res = await getDishListApi({
      page: unref(currentPage),
      limit: unref(pageSize),
      ...unref(searchParams)
    })

    try {
      res.data.map(row => (row.dish_images.sort((a, b) => a.localeCompare(b))))
      res.data.forEach(o => o.dish_images = o.dish_images.map(p => p.split('-').slice(1).join('-')))
      return {
        list: res.data || [],
        total: res.count || 0
      }
    } catch (err) {
      console.error('获取菜品列表失败：', err.message)
      return {
        list: [],
        total: 0
      }
    }
  },
  fetchDelApi: async (value) => {
    const res = await delDishListApi(value)
    return res.code === 200
  }
})

const { dataList, loading, total, pageSize, currentPage } = tableState
const { getList, delList, getSelections } = tableMethods

const IMPORT_STORAGE_KEY = 'IMPORT_DISH_PAYLOAD'
const DISH_PAGE_STATE_KEY = 'DISH_PAGE_STATE'

const mapDishRowToImport = (dish) => {
  if (!dish) return null
  const safeNumber = (value, fallback = null) => {
    if (value === null || value === undefined) return fallback
    const num = Number(value)
    return Number.isNaN(num) ? fallback : num
  }
  const images = Array.isArray(dish.dish_images) ? dish.dish_images.filter((img) => typeof img === 'string' && img) : []
  const normalizeImage = (img) => {
    if (typeof img !== 'string' || !img.length) return ''
    const [path] = img.split('?')
    return path ? `${path}?original` : ''
  }
  return {
    id: dish.id ?? undefined,
    name_unique: dish.name_unique ?? '',
    name_display: dish.name_display ?? dish.name_unique ?? '',
    name_english: dish.name_english ?? null,
    branch_id: safeNumber(dish.branch_id, 1),
    dish_category_id: safeNumber(dish.dish_category_id, 2),
    sale_price: dish.sale_price ?? null,
    order_number: dish.order_number ?? null,
    sku_code: dish.sku_code ?? null,
    status: safeNumber(dish.status, -1),
    dish_images_display: [...images],
    dish_images: images.map(normalizeImage).filter(Boolean),
    action: null
  }
}

const persistImportPayload = (rows) => {
  if (rows?.length) {
    sessionStorage.setItem(IMPORT_STORAGE_KEY, JSON.stringify(rows))
  } else {
    sessionStorage.removeItem(IMPORT_STORAGE_KEY)
  }
}

const tableColumns = reactive<TableColumn[]>([
  {
    field: 'selection',
    type: 'selection',
    show: true
  },
  {
    field: 'dish_image',
    label: '图片',
    show: true,
    disabled: true,
    width: '110px',
    slots: {
      default: (data: any) => {
        const row = data.row
        const hasImage = row.dish_images.length > 0
        const defaultImg = '/src/assets/imgs/no_image.png'
        return (
          <>
            <div class="resource-image-name flex items-center">
              <div>
                <ElImage
                  src={hasImage ? `${row.dish_images[0]}?x-oss-process=image/resize,m_fixed,h_100` : defaultImg}
                  zoom-rate={1.2}
                  preview-src-list={hasImage ? dataList.value.map(item => item.dish_images[0]) : []}
                  preview-teleported={true}
                  initial-index={data.$index}
                  style="height: 60px; display: block"
                  fix="cover"
                />
              </div>
            </div>
          </>
        )
      }
    }
  },
  {
    field: 'id',
    label: 'ID',
    show: false,
    disabled: false
  },
  {
    field: 'name_unique',
    label: '名称',
    minwidth: '240px',
    show: true,
    disabled: true
  },
  {
    field: 'name_display',
    label: '显示名称',
    minwidth: '240px',
    show: true,
    disabled: true
  },
  {
    field: 'branch_id',
    label: '所属门店id',
    width: '100px',
    show: false
  },
  {
    field: 'branch_name_unique',
    label: '所属门店',
    width: '160px',
    show: true,
    disabled: true
  },
  {
    field: 'dish_category_id',
    label: '分类id',
    width: '100px',
    show: false
  },
  {
    field: 'dish_category_name_unique',
    label: '分类',
    width: '160px',
    show: true,
    disabled: true
  },
  {
    field: 'sku_code',
    label: 'SKU码',
    width: '160px',
    show: true,
    disabled: true
  },
  {
    field: 'sale_price',
    label: '基础售价',
    width: '120px',
    show: true,
    disabled: true
  },
  {
    field: 'time_on',
    label: '首次上架日期',
    width: '140px',
    show: true,
    disabled: true
  },
  {
    field: 'time_off',
    label: '下架日期',
    width: '140px',
    show: true,
    disabled: true
  },
  {
    field: 'status',
    label: '状态',
    width: '100px',
    show: true,
    disabled: true,
    formatter: (row) => (dishStatusOptions.value.reduce((acc, item) =>({
      ...acc, 
      [item.value]: item.label
    }), {}))[row.status] || '未知'
  },
  {
    field: 'action',
    label: '操作',
    width: '140px',
    align: 'center',
    fixed: 'right',
    show: true,
    slots: {
      default: (data: any) => {
        const row = data.row
        const update = ['auth.product.dish.update']
        const del = ['auth.product.dish.delete']
        return (
          <>
            <BaseButton type="primary" v-hasPermi={update} link size="small" onClick={() => editAction(row)}>修改</BaseButton>
            <BaseButton type="danger" v-hasPermi={del} loading={delLoading.value} link size="small" onClick={() => delData(row)}>删除</BaseButton>
          </>
        )
      }
    }
  }
])

const branchOptions = ref<Array<{label: string, value: number}>>([])
const dishStatusOptions = ref<Array<{label: string, value: number}>>([])

// 处理表单字段变化，只更新lastSearchParams（表单显示值）
// searchParams只在点击"查询"按钮时更新（已执行的查询条件）
const handleFieldChange = (field: string, value: any) => {
  if (!pageReady.value) return
  
  // 只更新lastSearchParams（表单显示值），不更新searchParams
  if (!lastSearchParams.value) {
    lastSearchParams.value = {}
  }
  
  // 如果值不为空，保存；如果为空，删除该字段
  if (value !== null && value !== undefined && value !== '' && 
      !(Array.isArray(value) && value.length === 0)) {
    lastSearchParams.value[field] = value
  } else {
    delete lastSearchParams.value[field]
  }
}

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'branch_id',
    label: '店铺',
    component: 'Select',
    componentProps: {
      options: branchOptions.value,
      on: {
        change: (value: any) => {
          handleFieldChange('branch_id', value)
        }
      }
    }
  },
  {
    field: 'status',
    label: '状态',
    component: 'Select',
    componentProps: {
      options: dishStatusOptions.value,
      on: {
        change: (value: any) => {
          handleFieldChange('status', value)
        }
      }
    }
  },
  {
    field: 'fuzzy_query_str',
    label: '模糊查询',
    component: 'Input',
    componentProps: {
      clearable: true,
      style: {
        width: '400px'
      },
      on: {
        input: (value: any) => {
          handleFieldChange('fuzzy_query_str', value)
        },
        change: (value: any) => {
          handleFieldChange('fuzzy_query_str', value)
        }
      }
    }
  }
])

const getOptions = async () => {
  try {
    const res = await getBranchOptionsApi()
    if (!res?.data) {
      console.warn('返回门店列表为空')
      branchOptions.value = []
      return
    }
    branchOptions.value = res.data
      .filter(item => item?.is_active)
      .map(({ label, value}) => ({
        label: label || '未命名店铺',
        value: value || 0 }))
    Object.assign(searchSchema[0].componentProps, {
      options: branchOptions.value
    })
  } catch (err) {
    console.error('获取店铺列表失败：', err)
    branchOptions.value = []
  }

  try {
    const res = await getDishStatusOptionsApi()
    if (!res?.data) {
      console.warn('返回菜品状态列表为空')
      dishStatusOptions.value = []
      return
    }
    dishStatusOptions.value = res.data
    Object.assign(searchSchema[1].componentProps, {
      options: dishStatusOptions.value
    })
  } catch (err) {
    console.error('获取菜品状态列表失败：', err)
    dishStatusOptions.value = []
  }
}

// 保存页面状态到 sessionStorage
const savePageState = async () => {
  try {
    // 获取当前选中的行ID
    const selections = typeof getSelections === 'function' ? await getSelections() : []
    const selectedIds = selections.map((row: any) => row?.id).filter((id: any) => id !== undefined)
    
    // 使用toRaw确保获取原始值
    const formDisplayParams = toRaw(lastSearchParams.value) || {}
    const executedSearchParams = toRaw(searchParams.value) || {}
    
    // 确保dish_category_id包含在查询条件中
    if (curCategory.value !== null && curCategory.value !== undefined) {
      formDisplayParams.dish_category_id = curCategory.value
      executedSearchParams.dish_category_id = curCategory.value
    } else {
      // 如果分类为空，从查询条件中移除
      delete formDisplayParams.dish_category_id
      delete executedSearchParams.dish_category_id
    }
    
    const state = {
      formDisplayParams,      // 表单显示值（用户输入的所有条件，包括未执行的）
      executedSearchParams,   // 已执行的查询条件（只在点击"查询"按钮时更新）
      currentPage: currentPage.value,
      pageSize: pageSize.value,
      activeIndex: activeIndex.value,
      curCategory: curCategory.value,
      selectedIds: selectedIds
    }
    sessionStorage.setItem(DISH_PAGE_STATE_KEY, JSON.stringify(state))
  } catch (err) {
    console.error('保存页面状态失败：', err)
  }
}

// 从 sessionStorage 恢复页面状态
const restorePageState = () => {
  try {
    const cache = sessionStorage.getItem(DISH_PAGE_STATE_KEY)
    if (!cache) return null
    const state = JSON.parse(cache)
    return state
  } catch (err) {
    console.error('恢复页面状态失败：', err)
    return null
  }
}

// 恢复表格的selection状态
const restoreTableSelection = async (selectedIds: number[]) => {
  if (!selectedIds || !Array.isArray(selectedIds) || selectedIds.length === 0) return
  
  try {
    // 等待数据加载完成
    await nextTick()
    
    // 获取ElTable实例
    const elTable = await tableMethods.getElTableExpose()
    if (!elTable) return
    
    // 根据ID恢复选中状态
    selectedIds.forEach((id) => {
      const row = dataList.value.find((item: any) => item?.id === id)
      if (row) {
        elTable.toggleRowSelection(row, true)
      }
    })
  } catch (err) {
    console.error('恢复表格选择状态失败：', err)
  }
}

// 清除页面状态缓存
const clearPageState = () => {
  try {
    sessionStorage.removeItem(DISH_PAGE_STATE_KEY)
  } catch (err) {
    console.error('清除页面状态失败：', err)
  }
}

const searchParams = ref({})
// 保存最后一次搜索的查询条件，用于状态恢复
const lastSearchParams = ref<Record<string, any>>({})

const setSearchParams = async (data: any) => {
  currentPage.value = 1
  // 使用toRaw确保获取原始值
  const rawData = toRaw(data)
  
  // 确保dish_category_id包含在查询条件中（如果curCategory有值）
  if (curCategory.value !== null && curCategory.value !== undefined) {
    rawData.dish_category_id = curCategory.value
  }
  
  // 更新searchParams（已执行的查询条件）
  searchParams.value = {...rawData}
  
  // 同时更新lastSearchParams（表单显示值），确保表单显示与查询条件一致
  const filteredParams: Record<string, any> = {}
  Object.keys(rawData).forEach(key => {
    const value = rawData[key]
    // 只保存非空值
    if (value !== null && value !== undefined && value !== '' && 
        !(Array.isArray(value) && value.length === 0)) {
      filteredParams[key] = value
    }
  })
  lastSearchParams.value = filteredParams
  
  // 保存状态（包含已执行的查询条件）
  await savePageState()
  getList()
}

const configBase = async () => {
  const selections = typeof getSelections === 'function' ? await getSelections() : []
  if (!selections?.length) {
    persistImportPayload([])
    ElMessage.info('未选择菜品，将打开空白批量维护页')
    push('/product/dish/import')
    return
  }
  const payload = selections
    .map(mapDishRowToImport)
    .filter((item) => item !== null)
  if (!payload.length) {
    ElMessage.warning('所选菜品数据异常，已打开空白批量维护页')
    persistImportPayload([])
    push('/product/dish/import')
    return
  }
  persistImportPayload(payload)
  push('/product/dish/import')
}

const delLoading = ref(false)
const delData = async (row?: any) => {
  delLoading.value = true
  try {
    if (row) {
      await delList(true, [row.id])
    } else {
      await delList(true)
    }
    // 删除后只刷新表格数据，保持当前页码和选择状态
    await getList()
    savePageState()
  } finally {
    delLoading.value = false
  }
}

const dialogVisible = ref(false)
const dialogTitle = ref('')
const currentRow = ref()
const actionType = ref('')

const writeRef = ref<ComponentRef<typeof Write>>()
const saveLoading = ref(false)

const addAction = () => {
  dialogTitle.value = '新增菜品'
  actionType.value = 'add'
  currentRow.value = undefined
  dialogVisible.value = true
}

const editAction = async (row: any) => {
  const res = await getDishApi(row.id)
  if (res) {
    dialogTitle.value = '编辑菜品'
    actionType.value = 'edit'
    if (!res.data.dish_images) {
      res.data.dish_images_display = []
      res.data.dish_images = []
    }
    res.data.dish_images.sort((a, b) => a.localeCompare(b))
    res.data.dish_images = res.data.dish_images.map(item => item.split('-')[1])
    res.data.dish_images_display = res.data.dish_images
    res.data.dish_images = res.data.dish_images.map((item) => `${item}?original`)
    currentRow.value = res.data
    dialogVisible.value = true
  }
}

const uploadFile = async (file) => {
  try {
    const res = await fetch('/api/vadmin/system/upload/image/to/local', {
      method: 'POST',
      body: file
    })

    if (!res.ok) {
      throw new Error('HTTP错误！状态：${res.status}')
    }

    const data = await res.json()
    return {
      success: true,
      message: '上传成功',
      data: data
    }
  } catch (err) {
    let msg = ''
    if (err instanceof Error) {
      msg = err.message
    } else {
      msg = '未知的错误.'
    }
    return {
      success: false,
      message: msg
    }
  }
}

const save = async () => {
  const write = unref(writeRef)
  const formData = await write?.submit()
  if (formData) {
    saveLoading.value = true
    const keys = Object.keys(formData)
    for (let i = 0; i < keys.length; i++) {
      const key = keys[i]
      if (key === 'dish_images') {
        let index = 0
        for (let fileData of formData['dish_images']) {
          if (Array.isArray(formData['dish_images'][index])) {
            const fileForm = new FormData()
            fileForm.append('file', fileData[3].raw)
            fileForm.append('path', 'system')
            const res = await uploadFile(fileForm)
            if (!res.success) {
              throw new Error('图片上传错误：${res.message}[${res.status}]')
            }
            formData['dish_images'][index] = `${res.data.data.remote_path}?${fileData[1]}`
            formData['dish_images_display'][index] = `${res.data.data.remote_path}?${fileData[1]}`
          }
          index = index + 1
        }
      }
    }
    try {
      const res = ref({})
      if (actionType.value === 'add') {
        res.value = await addDishListApi(formData)
        if (res.value) {
          dialogVisible.value = false
          // 只刷新表格数据，保持当前页码和选择状态
          await getList()
          savePageState()
        }
      } else if (actionType.value === 'edit') {
        res.value = await putDishListApi(formData)
        if (res.value) {
          dialogVisible.value = false
          // 只刷新表格数据，保持当前页码和选择状态
          await getList()
          savePageState()
        }
      }
    } finally {
      saveLoading.value = false
    }
  } else {
  }
}

// 状态保存定时器
let saveStateTimer: ReturnType<typeof setTimeout> | null = null

// 页面加载状态，用于避免闪屏
const pageReady = ref(false)
// 状态恢复标志，防止恢复过程中触发watch
const isRestoring = ref(false)

onMounted(async () => {
  // 先不显示页面，等待状态恢复完成
  isRestoring.value = true
  
  // 先加载options，确保Select组件的选项可用
  await getOptions()
  
  const state = restorePageState()
  if (state) {
    // 恢复分页状态（同步操作，立即生效）
    if (typeof state.currentPage === 'number' && state.currentPage > 0) {
      currentPage.value = state.currentPage
    }
    if (typeof state.pageSize === 'number' && state.pageSize > 0) {
      pageSize.value = state.pageSize
    }
    
    // 恢复查询条件
    // 1. 恢复表单显示值（formDisplayParams）
    // 2. 使用已执行的查询条件（executedSearchParams）执行查询
    if (state.formDisplayParams || state.executedSearchParams) {
      // 恢复表单显示值
      if (state.formDisplayParams && Object.keys(state.formDisplayParams).length > 0) {
        lastSearchParams.value = { ...state.formDisplayParams }
        
        // 等待Search组件注册后恢复表单显示
        const restoreFormDisplay = async () => {
          let retries = 0
          while (retries < 20 && (!searchRegistered.value || !search.value)) {
            await new Promise(resolve => setTimeout(resolve, 50))
            retries++
          }
          
          if (search.value && typeof search.value.setValues === 'function') {
            await nextTick()
            await nextTick()
            await search.value.setValues(state.formDisplayParams)
          }
        }
        
        if (searchRegistered.value && search.value) {
          restoreFormDisplay()
        } else {
          pendingSearchParams.value = state.formDisplayParams
        }
      }
      
      // 使用已执行的查询条件执行查询
      if (state.executedSearchParams && Object.keys(state.executedSearchParams).length > 0) {
        searchParams.value = { ...state.executedSearchParams }
      } else {
        // 如果没有已执行的查询条件，使用空查询条件
        searchParams.value = {}
      }
      
      // 恢复菜品分类（优先从查询条件中恢复，兼容旧数据）
      let categoryId: number | null = null
      if (state.executedSearchParams?.dish_category_id !== undefined) {
        categoryId = state.executedSearchParams.dish_category_id
      } else if (state.curCategory !== undefined) {
        categoryId = state.curCategory
      }
      
      if (categoryId !== null && categoryId !== undefined) {
        curCategory.value = categoryId
        activeIndex.value = categoryId.toString()
      } else {
        curCategory.value = null
        activeIndex.value = '0'
      }
    } else {
      // 如果没有查询条件，恢复分类状态
      if (state.activeIndex !== undefined) {
        activeIndex.value = state.activeIndex
      }
      if (state.curCategory !== undefined) {
        curCategory.value = state.curCategory
      }
    }
    
    // 触发数据加载（使用已执行的查询条件）
    await getList()
    
    // 数据加载完成后，恢复表格selection状态
    if (state.selectedIds && Array.isArray(state.selectedIds) && state.selectedIds.length > 0) {
      await nextTick()
      restoreTableSelection(state.selectedIds)
    }
  } else {
    // 如果没有恢复的状态，正常初始化
    await getList()
  }
  
  // 状态恢复完成，显示页面
  isRestoring.value = false
  pageReady.value = true
})

// 监听options变化，确保在options加载完成后恢复表单显示
watch(
  [() => branchOptions.value.length, () => dishStatusOptions.value.length, () => searchRegistered.value],
  async () => {
    // 如果options已加载、Search组件已注册且有pendingSearchParams，恢复表单显示
    if (
      pendingSearchParams.value && 
      branchOptions.value.length > 0 && 
      dishStatusOptions.value.length > 0 &&
      searchRegistered.value &&
      search.value &&
      typeof search.value.setValues === 'function'
    ) {
      await nextTick()
      await nextTick()
      try {
        await search.value.setValues(pendingSearchParams.value)
        lastSearchParams.value = { ...pendingSearchParams.value }
        pendingSearchParams.value = null
      } catch (err) {
        console.error('恢复Search组件值失败（options加载后）：', err)
      }
    }
  },
  { immediate: false }
)

// 监听数据列表、分页、分类变化，自动保存状态（debounce）
watch(
  [() => dataList.value, () => currentPage.value, () => pageSize.value, () => activeIndex.value, () => curCategory.value],
  async () => {
    // 如果正在恢复状态，不触发保存，避免多次刷新
    if (pageReady.value && !isRestoring.value) {
      if (saveStateTimer) {
        clearTimeout(saveStateTimer)
      }
      saveStateTimer = setTimeout(async () => {
        await savePageState()
      }, 500)
    }
  },
  { deep: true }
)

// 组件卸载前保存状态
onBeforeUnmount(() => {
  if (saveStateTimer) {
    clearTimeout(saveStateTimer)
  }
  savePageState()
})
</script>

<template>
  <ContentWrap v-show="pageReady">
    <Search ref="search" :schema="searchSchema" :showReset="true" @register="handleSearchRegister" @reset="setSearchParams" @search="setSearchParams" />
    <div class="content-area">
      <el-card
        class="left-list" header="菜品分类" shadow="never">
        <el-menu
          header="菜品分类"
          class="left-list"
          shadow="never"
          :default-active="activeIndex.toString()"
          @select="handleSelect"
        >
          <el-menu-item
            v-for="category in categories"
            :key="category.id"
            :index="category.id.toString()"
          >
            {{ category.name_unique }}<span v-if="category.dish_count > 0">[{{ category.dish_count }}]</span>
          </el-menu-item>
        </el-menu>
      </el-card>
      <div class="right-table">
        <Table
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          showAction
          :columns="tableColumns"
          default-expand-all
          node-key="id"
          :data="dataList"
          :loading="loading"
          :pagination="{
            total
          }"
          @register="tableRegister"
          @refresh="getList"
        >
          <template #toolbar>
            <ElRow :gutter="10">
              <ElCol :span="1.5" v-hasPermi="['auth.product.dish.create']">
                <ButtonPlus stype="new" @click="addAction" />
                <ButtonPlus stype="batch" @click="configBase()" >维护</ButtonPlus>
                <ButtonPlus stype="setting" @click="configDish()" >菜品</ButtonPlus>
                <ButtonPlus stype="batch" @click="delData(null)" >删除</ButtonPlus>
              </ElCol>
            </ElRow>
          </template>
        </Table>
      </div>
    </div>
  </ContentWrap>

  <Dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    :height="'660px'"
    :width="'700px'"
  >
    <Write
      v-if="actionType === 'add' || actionType === 'edit'"
      ref="writeRef"
      :dialog-visible="dialogVisible"
      :current-row="currentRow"
      :dish-status-options="dishStatusOptions"
    />

    <template #footer v-if="actionType === 'add' || actionType === 'edit'">
      <ButtonPlus stype="save" :loading="saveLoading" @click="save" />
      <ButtonPlus stype="return" @click="dialogVisible = false" />
    </template>
  </Dialog>
</template>

<style scoped>
.content-area {
  display: flex;
}

.left-list {
  width: 160px;
  margin-right: 10px;
  flex-shrink: 0;
}

.right-table {
  flex: 1;
  overflow-x: auto;
}
</style>



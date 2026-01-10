<script setup lang="tsx">
import { reactive, ref, unref, toRaw, onMounted, watch, onBeforeUnmount, nextTick } from 'vue'
import {
  getDishListApi,
  addDishListApi,
  delDishListApi,
  putDishListApi,
  getDishApi,
  getDishStatusOptionsApi
} from '@/api/vadmin/product/dish'
import { getKitchenListApi } from '@/api/vadmin/product/kitchen'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { useTable } from '@/hooks/web/useTable'
import { Table, TableColumn } from '@/components/Table'
import { ButtonPlus } from '@/components/ButtonPlus'
import { ElRow, ElCol, ElImage, ElMenu, ElMenuItem, ElCard, ElMessage } from 'element-plus'
import { Dialog } from '@/components/Dialog'
import Response from './components/Response.vue'
import { BaseButton } from '@/components/Button'
import { useRouter } from 'vue-router'
import { ImagePlus } from '@/components/ImagePlus'
import { ResponseDrawer } from '@/wintemplate/ResponseDrawer'

defineOptions({
  name: 'ProductDish'
})

// ==================== 常量定义 ====================
const IMPORT_STORAGE_KEY = 'IMPORT_DISH_PAYLOAD'
const DISH_PAGE_STATE_KEY = 'DISH_PAGE_STATE'
const DEFAULT_IMAGE = '/src/assets/imgs/no_image.png'

// ==================== 路由和工具 ====================
const { push } = useRouter()

// ==================== 状态管理 ====================
// 厨部相关
const kitchens = ref([])
const activeIndex = ref(0)
const curKitchen = ref(null)

// 搜索相关
const search = ref(null)
const searchRegistered = ref(false)
const pendingSearchParams = ref<any>(null)
const searchParams = ref({})
const lastSearchParams = ref<Record<string, any>>({})
const pageReady = ref(false)
const isRestoring = ref(false)

// 对话框相关
const dialogVisible = ref(false)
const dialogTitle = ref('')
const currentRow = ref()
const actionType = ref('')
const responseRef = ref<ComponentRef<typeof Response>>()
const saveLoading = ref(false)
const delLoading = ref(false)

// 选项数据
const dishStatusOptions = ref<Array<{ label: string; value: number }>>([])

// 状态保存定时器
let saveStateTimer: ReturnType<typeof setTimeout> | null = null

// ImagePlus 组件实例（用于调用规范化方法）
const imagePlusHelperRef = ref<InstanceType<typeof ImagePlus>>()

// ==================== 测试抽屉弹窗 ====================
/** 测试抽屉显示状态 */
const testDrawerVisible = ref(false)
/** 测试抽屉组件引用 */
const testDrawerRef = ref<InstanceType<typeof ResponseDrawer>>()

/**
 * 打开测试抽屉
 */
const openTestDrawer = () => {
  testDrawerVisible.value = true
}

/**
 * 关闭测试抽屉
 */
const closeTestDrawer = () => {
  testDrawerVisible.value = false
}

// ==================== 工具函数 ====================
/**
 * 安全转换数字
 */
const safeNumber = (value: any, fallback: number | null = null): number | null => {
  if (value === null || value === undefined) return fallback
  const num = Number(value)
  return Number.isNaN(num) ? fallback : num
}


/**
 * 过滤空值参数
 */
const filterEmptyParams = (params: Record<string, any>): Record<string, any> => {
  const filtered: Record<string, any> = {}
  Object.keys(params).forEach((key) => {
    const value = params[key]
    if (
      value !== null &&
      value !== undefined &&
      value !== '' &&
      !(Array.isArray(value) && value.length === 0)
    ) {
      filtered[key] = value
    }
  })
  return filtered
}

// ==================== 数据转换函数 ====================
/**
 * 将菜品行数据转换为导入格式
 */
const mapDishRowToImport = (dish: any) => {
  if (!dish) return null

  // 使用 ImagePlus 组件实例的规范化方法处理图片路径
  const normalizedImages = (imagePlusHelperRef.value as any)?.getNormalizedImages?.(dish.dish_images) || []

  return {
    id: dish.id ?? undefined,
    name_unique: dish.name_unique ?? '',
    name_display: dish.name_display ?? dish.name_unique ?? '',
    name_english: dish.name_english ?? null,
    kitchen_id: safeNumber(dish.kitchen_id, 1),
    spec: dish.spec ?? null,
    unit: dish.unit ?? null,
    price: dish.price ?? null,
    order_number: dish.order_number ?? null,
    status: safeNumber(dish.status, -1),
    // dish_images_display 由 ImagePlus 组件内部自动维护，不需要手动设置
    // 使用 ImagePlus 组件提供的规范化函数处理图片路径（自动过滤删除标记和未上传的图片）
    dish_images: normalizedImages,
    action: null
  }
}

// ==================== 数据获取函数 ====================
/**
 * 获取厨部列表
 */
const fetchKitchens = async () => {
  const res = await getKitchenListApi({ is_active: true })
  if (!res?.data) {
    kitchens.value = []
    return
  }
  kitchens.value = [{ id: 0, name_unique: '（全部）' }, ...res.data]
}

/**
 * 获取菜品状态选项
 */
const getOptions = async () => {
  try {
    const res = await getDishStatusOptionsApi()
    if (!res?.data) {
      console.warn('返回菜品状态列表为空')
      dishStatusOptions.value = []
      return
    }
    dishStatusOptions.value = res.data
    // 更新状态字段的选项（searchSchema[0] 是状态字段）
    Object.assign(searchSchema[0].componentProps, {
      options: dishStatusOptions.value
    })
  } catch (err) {
    console.error('获取菜品状态列表失败：', err)
    dishStatusOptions.value = []
  }
}

// ==================== 事件处理函数 ====================
/**
 * 监听Search组件的register事件
 */
const handleSearchRegister = async () => {
  searchRegistered.value = true

  // 如果有待恢复的表单显示值，立即设置
  if (pendingSearchParams.value && search.value && typeof search.value.setValues === 'function') {
    await nextTick()
    await nextTick()
    try {
      await (search.value as any).setValues(pendingSearchParams.value)
      lastSearchParams.value = { ...pendingSearchParams.value }
      pendingSearchParams.value = null
    } catch (err) {
      console.error('恢复Search组件值失败：', err)
    }
  }
}

/**
 * 处理厨部选择
 */
const handleSelect = (index: string) => {
  const selected = kitchens.value.find((c) => c.id.toString() === index)
  if (selected) {
    activeIndex.value = index
    curKitchen.value = index > '0' ? parseInt(index, 10) : null
  } else {
    curKitchen.value = null
  }

  // 用显示值（lastSearchParams）代替查询值（searchParams），然后更新 kitchen_id
  const displayParams = toRaw(lastSearchParams.value) || {}
  const newSearchParams: Record<string, any> = { ...displayParams }
  const kitchenId = curKitchen.value

  // 更新 kitchen_id
  if (kitchenId !== null && kitchenId !== undefined) {
    newSearchParams.kitchen_id = kitchenId
  } else {
    delete newSearchParams.kitchen_id
  }

  // 更新实际查询参数和表单显示值
  searchParams.value = newSearchParams
  if (!lastSearchParams.value) {
    lastSearchParams.value = {}
  }
  if (kitchenId !== null && kitchenId !== undefined) {
    lastSearchParams.value.kitchen_id = kitchenId
  } else {
    delete lastSearchParams.value.kitchen_id
  }

  // 保存状态并执行查询
  savePageState()
  getList()
}

/**
 * 处理表单字段变化，只更新lastSearchParams（表单显示值）
 */
const handleFieldChange = (field: string, value: any) => {
  if (!pageReady.value) return

  if (!lastSearchParams.value) {
    lastSearchParams.value = {}
  }

  // 如果值不为空，保存；如果为空，删除该字段
  if (
    value !== null &&
    value !== undefined &&
    value !== '' &&
    !(Array.isArray(value) && value.length === 0)
  ) {
    lastSearchParams.value[field] = value
  } else {
    delete lastSearchParams.value[field]
  }
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
      res.data.map((row) => row.dish_images.sort((a, b) => a.localeCompare(b)))
      res.data.forEach(
        (o) => (o.dish_images = o.dish_images.map((p) => p.split('-').slice(1).join('-')))
      )
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

// ==================== 表格列定义 ====================
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
    showConfig: false, // 不可配置，固定显示
    width: '110px',
    slots: {
      default: (data: any) => {
        const row = data.row
        const hasImage = row.dish_images.length > 0
        return (
          <div class="resource-image-name flex items-center">
            <div>
              <ElImage
                src={
                  hasImage
                    ? `${row.dish_images[0]}?x-oss-process=image/resize,m_fixed,h_100`
                    : DEFAULT_IMAGE
                }
                zoom-rate={1.2}
                preview-src-list={hasImage ? dataList.value.map((item) => item.dish_images[0]) : []}
                preview-teleported={true}
                initial-index={data.$index}
                style="height: 60px; display: block"
                fit="cover"
              />
            </div>
          </div>
        )
      }
    }
  },
  {
    field: 'id',
    label: 'ID',
    show: false,
    showConfig: true // 可配置显示/隐藏
  },
  {
    field: 'name_unique',
    label: '名称',
    minwidth: '240px',
    show: true,
    showConfig: false // 不可配置，固定显示
  },
  {
    field: 'name_display',
    label: '显示名称',
    minwidth: '240px',
    show: true,
    showConfig: true // 可配置显示/隐藏
  },
  {
    field: 'kitchen_id',
    label: '分类id',
    width: '100px',
    show: false
  },
  {
    field: 'kitchen_name_unique',
    label: '分类',
    width: '160px',
    show: true,
    showConfig: false // 不可配置，固定显示
  },
  {
    field: 'spec',
    label: '规格',
    width: '160px',
    show: true,
    showConfig: false // 不可配置，固定显示
  },
  {
    field: 'unit',
    label: '单位',
    width: '160px',
    show: true,
    showConfig: false // 不可配置，固定显示
  },
  {
    field: 'price',
    label: '基础售价',
    width: '120px',
    show: true,
    showConfig: false // 不可配置，固定显示
  },
  {
    field: 'time_on',
    label: '首次上架日期',
    width: '140px',
    show: true,
    showConfig: false // 不可配置，固定显示
  },
  {
    field: 'time_off',
    label: '下架日期',
    width: '140px',
    show: true,
    showConfig: false // 不可配置，固定显示
  },
  {
    field: 'status',
    label: '状态',
    width: '100px',
    show: true,
    showConfig: false, // 不可配置，固定显示
    formatter: (row) =>
      dishStatusOptions.value.reduce(
        (acc, item) => ({
          ...acc,
          [item.value]: item.label
        }),
        {}
      )[row.status] || '未知'
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
            <BaseButton
              type="primary"
              v-hasPermi={update}
              link
              size="small"
              onClick={() => editAction(row)}
            >
              修改
            </BaseButton>
            <BaseButton
              type="danger"
              v-hasPermi={del}
              loading={delLoading.value}
              link
              size="small"
              onClick={() => delData(row)}
            >
              删除
            </BaseButton>
          </>
        )
      }
    }
  }
])

const searchSchema = reactive<FormSchema[]>([
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

// ==================== 查询参数管理 ====================
/**
 * 设置搜索参数并执行查询
 */
const setSearchParams = async (data: any) => {
  currentPage.value = 1
  const rawData = toRaw(data)

  // 确保kitchen_id包含在查询条件中（如果curKitchen有值）
  if (curKitchen.value !== null && curKitchen.value !== undefined) {
    rawData.kitchen_id = curKitchen.value
  }

  // 更新searchParams（已执行的查询条件）
  searchParams.value = { ...rawData }

  // 同时更新lastSearchParams（表单显示值），确保表单显示与查询条件一致
  lastSearchParams.value = filterEmptyParams(rawData)

  // 保存状态（包含已执行的查询条件）
  await savePageState()
  getList()
}

// ==================== 业务操作函数 ====================
/**
 * 打开批量维护页面
 */
const configBase = async () => {
  const selections = typeof getSelections === 'function' ? await getSelections() : []
  if (!selections?.length) {
    persistImportPayload([])
    ElMessage.info('未选择菜品，将打开空白批量维护页')
    push('/system/test/import')
    return
  }
  const payload = selections.map(mapDishRowToImport).filter((item) => item !== null)
  if (!payload.length) {
    ElMessage.warning('所选菜品数据异常，已打开空白批量维护页')
    persistImportPayload([])
    push('/system/test/import')
    return
  }
  persistImportPayload(payload)
  push('/system/test/import')
}

/**
 * 删除数据
 */
const delData = async (row?: any) => {
  delLoading.value = true
  try {
    if (row) {
      await delList(true, [row.id])
    } else {
      await delList(true)
    }
    await getList()
    savePageState()
  } finally {
    delLoading.value = false
  }
}

/**
 * 打开新增对话框
 */
const addAction = () => {
  dialogTitle.value = '新增菜品'
  actionType.value = 'add'
  currentRow.value = undefined
  dialogVisible.value = true
}

/**
 * 打开编辑对话框
 */
const editAction = async (row: any) => {
  const res = await getDishApi(row.id)
  if (res) {
    dialogTitle.value = '编辑菜品'
    actionType.value = 'edit'
    if (!res.data.dish_images) {
      res.data.dish_images = []
    }
    res.data.dish_images.sort((a, b) => a.localeCompare(b))
    res.data.dish_images = res.data.dish_images.map((item) => item.split('-')[1])
    // 标记为 original（组件内部会自动生成显示列表）
    res.data.dish_images = res.data.dish_images.map((item) => `${item}?original`)
    currentRow.value = res.data
    dialogVisible.value = true
  }
}

/**
 * 保存表单数据（新增或编辑）
 * 注意：图片上传已在 Response.vue 的 submit 方法中通过 ImagePlus 组件处理
 */
const save = async () => {
  const response = unref(responseRef)
  const formData = await response?.submit()
  if (!formData) return

  saveLoading.value = true
  try {
    // 根据操作类型调用不同的API
    const isAdd = actionType.value === 'add'
    const api = isAdd ? addDishListApi : putDishListApi
    const res = await api(formData)

    if (res) {
      dialogVisible.value = false
      await getList()
      savePageState()
    }
  } finally {
    saveLoading.value = false
  }
}

// ==================== 状态管理函数 ====================
/**
 * 保存页面状态到 sessionStorage
 */
const savePageState = async () => {
  try {
    // 获取当前选中的行ID
    const selections = typeof getSelections === 'function' ? await getSelections() : []
    const selectedIds = selections.map((row: any) => row?.id).filter((id: any) => id !== undefined)

    const formDisplayParams = toRaw(lastSearchParams.value) || {}
    const executedSearchParams = toRaw(searchParams.value) || {}

    // 确保kitchen_id包含在查询条件中
    if (curKitchen.value !== null && curKitchen.value !== undefined) {
      formDisplayParams.kitchen_id = curKitchen.value
      executedSearchParams.kitchen_id = curKitchen.value
    } else {
      delete formDisplayParams.kitchen_id
      delete executedSearchParams.kitchen_id
    }

    const state = {
      formDisplayParams, // 表单显示值（用户输入的所有条件，包括未执行的）
      executedSearchParams, // 已执行的查询条件（只在点击"查询"按钮时更新）
      currentPage: currentPage.value,
      pageSize: pageSize.value,
      activeIndex: activeIndex.value,
      curKitchen: curKitchen.value,
      selectedIds: selectedIds
    }
    sessionStorage.setItem(DISH_PAGE_STATE_KEY, JSON.stringify(state))
  } catch (err) {
    console.error('保存页面状态失败：', err)
  }
}

/**
 * 从 sessionStorage 恢复页面状态
 */
const restorePageState = () => {
  try {
    const cache = sessionStorage.getItem(DISH_PAGE_STATE_KEY)
    if (!cache) return null
    return JSON.parse(cache)
  } catch (err) {
    console.error('恢复页面状态失败：', err)
    return null
  }
}

/**
 * 恢复表格的selection状态
 */
const restoreTableSelection = async (selectedIds: number[]) => {
  if (!selectedIds || !Array.isArray(selectedIds) || selectedIds.length === 0) return

  try {
    await nextTick()
    const elTable = await tableMethods.getElTableExpose()
    if (!elTable) return

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

/**
 * 持久化导入数据
 */
const persistImportPayload = (rows: any[]) => {
  if (rows?.length) {
    sessionStorage.setItem(IMPORT_STORAGE_KEY, JSON.stringify(rows))
  } else {
    sessionStorage.removeItem(IMPORT_STORAGE_KEY)
  }
}

// ==================== 状态恢复逻辑 ====================
/**
 * 恢复分页状态
 */
const restorePagination = (state: any) => {
  if (typeof state.currentPage === 'number' && state.currentPage > 0) {
    currentPage.value = state.currentPage
  }
  if (typeof state.pageSize === 'number' && state.pageSize > 0) {
    pageSize.value = state.pageSize
  }
}

/**
 * 恢复表单显示值
 */
const restoreFormDisplay = async (formDisplayParams: Record<string, any>) => {
  if (!formDisplayParams || Object.keys(formDisplayParams).length === 0) return

  lastSearchParams.value = { ...formDisplayParams }

  const setFormValues = async () => {
    let retries = 0
    while (retries < 20 && (!searchRegistered.value || !search.value)) {
      await new Promise((resolve) => setTimeout(resolve, 50))
      retries++
    }

    if (search.value && typeof search.value.setValues === 'function') {
      await nextTick()
      await nextTick()
      await search.value.setValues(formDisplayParams)
    }
  }

  if (searchRegistered.value && search.value) {
    setFormValues()
  } else {
    pendingSearchParams.value = formDisplayParams
  }
}

/**
 * 恢复厨房选择状态
 */
const restoreKitchenState = (state: any) => {
  let kitchenId: number | null = null
  if (state.executedSearchParams?.kitchen_id !== undefined) {
    kitchenId = state.executedSearchParams.kitchen_id
  } else if (state.executedSearchParams?.dish_kitchen_id !== undefined) {
    // 兼容旧数据格式
    kitchenId = state.executedSearchParams.dish_kitchen_id
  } else if (state.curKitchen !== undefined) {
    kitchenId = state.curKitchen
  }

  if (kitchenId !== null && kitchenId !== undefined) {
    curKitchen.value = kitchenId
    activeIndex.value = kitchenId.toString()
  } else {
    curKitchen.value = null
    activeIndex.value = '0'
  }
}

/**
 * 初始化页面状态
 */
const initPageState = async () => {
  isRestoring.value = true
  await getOptions()

  const state = restorePageState()
  if (state) {
    restorePagination(state)

    if (state.formDisplayParams || state.executedSearchParams) {
      await restoreFormDisplay(state.formDisplayParams)

      if (state.executedSearchParams && Object.keys(state.executedSearchParams).length > 0) {
        searchParams.value = { ...state.executedSearchParams }
      } else {
        searchParams.value = {}
      }

      restoreKitchenState(state)
    } else {
      if (state.activeIndex !== undefined) {
        activeIndex.value = state.activeIndex
      }
      if (state.curKitchen !== undefined) {
        curKitchen.value = state.curKitchen
      }
    }

    await getList()

    if (state.selectedIds && Array.isArray(state.selectedIds) && state.selectedIds.length > 0) {
      await nextTick()
      restoreTableSelection(state.selectedIds)
    }
  } else {
    await getList()
  }

  isRestoring.value = false
  pageReady.value = true
}

// ==================== 生命周期 ====================
onMounted(() => {
  initPageState()
})

// ==================== 监听器 ====================
/**
 * 监听数据变化，自动保存状态（debounce）
 */
watch(
  [
    () => dataList.value,
    () => currentPage.value,
    () => pageSize.value,
    () => activeIndex.value,
    () => curKitchen.value
  ],
  async () => {
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

// ==================== 组件卸载 ====================
onBeforeUnmount(() => {
  if (saveStateTimer) {
    clearTimeout(saveStateTimer)
  }
  savePageState()
})

// ==================== 初始化 ====================
// 初始化时获取厨部列表
fetchKitchens()
</script>

<template>
  <ContentWrap v-show="pageReady">
    <Search
      ref="search"
      :schema="searchSchema"
      :showReset="true"
      @register="handleSearchRegister"
      @reset="setSearchParams"
      @search="setSearchParams"
    />
    <div class="content-area">
      <el-card class="left-list" header="厨部" shadow="never">
        <el-menu
          header="厨部"
          class="left-list"
          shadow="never"
          :default-active="activeIndex.toString()"
          @select="handleSelect"
        >
          <el-menu-item
            v-for="kitchen in kitchens"
            :key="kitchen.id"
            :index="kitchen.id.toString()"
          >
            {{ kitchen.name_unique
            }}<span v-if="kitchen.dish_count > 0">[{{ kitchen.dish_count }}]</span>
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
              <ElCol v-hasPermi="['auth.product.dish.create']" :span="1.5">
                <ButtonPlus stype="new" @click="addAction" />
                <ButtonPlus stype="batch" @click="configBase()">维护</ButtonPlus>
                <ButtonPlus stype="batch" @click="delData(null)">删除</ButtonPlus>
                <ButtonPlus stype="select" @click="openTestDrawer">测试抽屉弹窗</ButtonPlus>
              </ElCol>
            </ElRow>
          </template>
        </Table>
      </div>
    </div>
  </ContentWrap>

  <Dialog v-model="dialogVisible" :title="dialogTitle" :height="'660px'" :width="'700px'">
    <Response
      v-if="actionType === 'add' || actionType === 'edit'"
      ref="responseRef"
      :dialog-visible="dialogVisible"
      :current-row="currentRow"
      :dish-status-options="dishStatusOptions"
    />

    <template #footer v-if="actionType === 'add' || actionType === 'edit'">
      <ButtonPlus stype="save" :loading="saveLoading" @click="save" />
      <ButtonPlus stype="return" @click="dialogVisible = false" />
    </template>
  </Dialog>

  <!-- 隐藏的 ImagePlus 组件实例，用于调用规范化方法 -->
  <div style="display: none">
    <ImagePlus ref="imagePlusHelperRef" :model-value="[]" />
  </div>

  <!-- 测试抽屉弹窗 -->
  <ResponseDrawer
    ref="testDrawerRef"
    v-model="testDrawerVisible"
    title="测试抽屉弹窗"
    @close="closeTestDrawer"
    @cancel="closeTestDrawer"
  >
    <div style="padding: 20px">
      <h2>这是测试抽屉弹窗的内容区</h2>
      <p>您可以在内容区添加任何需要的内容。</p>
      <p>工具栏左侧显示 PrompInfo 组件，右侧显示返回按钮和其他可配置的按钮。</p>
    </div>
  </ResponseDrawer>
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

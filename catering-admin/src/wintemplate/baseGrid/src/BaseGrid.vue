<script setup lang="tsx">
import { unref, ref, reactive, watch, onMounted, nextTick } from 'vue'
import { useTable } from '@/hooks/web/useTable'
import { Table, TableColumn } from '@/components/Table'
import { ElImage, ElCard, ElMenu, ElMenuItem } from 'element-plus'
import { BaseButton } from '@/components/Button'
import { ButtonPre } from '@/components/ButtonPre'
import { PrompInfo } from '@/components/PrompInfo'
import { QueryBar, type QueryCondition } from '@/components/QueryBar'

defineOptions({
  name: 'BaseGrid'
})

// ==================== 常量定义 ====================
/** 默认图片路径 */
const DEFAULT_IMAGE = '/src/assets/imgs/no_image.png'

// ==================== 类型定义 ====================
/** ButtonPre 组件的按钮类型 */
type ButtonPreSType =
  | 'new'
  | 'modify'
  | 'delete'
  | 'save'
  | 'copy'
  | 'batch'
  | 'query'
  | 'select'
  | 'refresh'
  | 'ok'
  | 'cancel'
  | 'import'
  | 'export'
  | 'print'
  | 'setting'
  | 'return'
  | 'normal'

/** 操作按钮选项 */
interface ActionOption {
  type: 'edit' | 'delete' | 'other' // 操作类型
  label?: string // 自定义按钮文字
  onClick?: (row: any) => void // 点击事件回调
  permission?: string[] // 权限控制
  [key: string]: any // 其他按钮属性
}

/** 工具栏按钮配置 */
interface ToolbarButton {
  stype: ButtonPreSType // 按钮类型
  label?: string // 自定义按钮文字
  onClick?: () => void // 点击事件回调
  permission?: string[] // 权限控制
  [key: string]: any // 其他按钮属性
}

/** 表格列配置 */
interface GridColumn {
  field: string // 字段名
  label: string // 列标题
  type?: 'selection' | 'image' | 'text' | 'status' | 'action' // 列类型
  width?: string | number // 列宽度
  minWidth?: string | number // 最小宽度
  align?: 'left' | 'center' | 'right' // 对齐方式
  fixed?: boolean | 'left' | 'right' // 固定列
  show?: boolean // 是否显示
  showConfig?: boolean // 是否可配置显示/隐藏：true=可在右上角配置显示/隐藏，false=不可配置，固定显示。默认值为 true（可配置）
  formatter?: (row: any) => any // 格式化函数
  // 图片列专用配置
  imageField?: string // 图片字段名，默认使用 field
  imageListField?: string // 图片列表字段名，用于预览
  imageHeight?: string // 图片显示高度
  // 状态列专用配置
  statusOptions?: Array<{ label: string; value: any }> | (() => Array<{ label: string; value: any }>) // 状态映射选项
  // 操作列专用配置
  actionSlots?: (data: any) => JSX.Element | JSX.Element[] | null // 自定义操作插槽
  actionOptions?: ActionOption[] // 操作按钮配置
  onEdit?: (row: any) => void // 编辑回调
  onDelete?: (row: any) => void // 删除回调
}

/** 查询条件配置（使用 QueryCondition 类型） */
type SearchCondition = QueryCondition

/** 快捷查询列表项 */
interface QuickQueryItem {
  id: number | string | null // 项的唯一标识（null 表示"全部"选项）
  label: string // 显示名称
  [key: string]: any // 其他属性
}

/** 快捷查询列表配置 */
interface QuickQueryList {
  title: string // 列表标题
  data: QuickQueryItem[] | (() => Promise<QuickQueryItem[]>) // 数据数组或异步获取函数
  field: string // 查询字段名（用于更新查询参数）
  showAllOption?: boolean // 是否显示"（全部）"选项，默认 true
  allOptionLabel?: string // "（全部）"选项的显示文字，默认 "（全部）"
  allOptionValue?: number | string | null // "（全部）"选项的值，默认 null
}

/** 组件 Props */
interface Props {
  columns: GridColumn[] // 列配置数组
  fetchDataApi: (params: { page: number; limit: number; [key: string]: any }) => Promise<{ data: any[]; count: number }> // 数据获取接口
  fetchDelApi?: (ids: string[] | number[] | number | string) => Promise<boolean> // 删除接口（可选）
  nodeKey?: string // 行键，用于多选，默认 'id'
  showAction?: boolean // 是否显示操作栏，默认 false
  reserveSelection?: boolean // 是否保留选择（分页后保留），默认 false
  searchParams?: Record<string, any> // 搜索参数（已废弃，使用 searchConditions 替代）
  toolbarButtons?: ToolbarButton[] // 工具栏按钮配置
  searchConditions?: SearchCondition[] // 查询条件配置
  quickQueryList?: QuickQueryList // 左侧快捷查询列表配置
}

// ==================== Props 定义 ====================
const props = withDefaults(defineProps<Props>(), {
  nodeKey: 'id',
  showAction: false,
  reserveSelection: false,
  searchParams: () => ({}),
  searchConditions: () => []
})

// ==================== 查询条件 ====================
/** 查询参数（内部使用） */
const internalSearchParams = ref<Record<string, any>>({})

/**
 * 处理查询
 */
const handleSearch = (data: any) => {
  internalSearchParams.value = { ...data }
  currentPage.value = 1
  getList()
}

/**
 * 处理重置
 */
const handleReset = () => {
  internalSearchParams.value = {}
  currentPage.value = 1
  getList()
}

// ==================== 快捷查询列表 ====================
/** 快捷查询列表数据 */
const quickQueryData = ref<QuickQueryItem[]>([])
/** 当前选中的快捷查询项索引 */
const activeQuickQueryIndex = ref<string>('0')

/**
 * 初始化快捷查询列表
 */
const initQuickQueryList = async () => {
  if (!props.quickQueryList) {
    return
  }

  const config = props.quickQueryList
  let data: QuickQueryItem[] = []

  // 获取数据
  if (typeof config.data === 'function') {
    try {
      data = await config.data()
    } catch (err) {
      console.error('获取快捷查询列表数据失败：', err)
      data = []
    }
  } else {
    data = config.data || []
  }

  // 添加"（全部）"选项
  const showAllOption = config.showAllOption !== false // 默认显示
  if (showAllOption) {
    const allOption: QuickQueryItem = {
      id: config.allOptionValue !== undefined ? config.allOptionValue : null,
      label: config.allOptionLabel || '（全部）'
    }
    quickQueryData.value = [allOption, ...data]
  } else {
    quickQueryData.value = data
  }

  // 初始化选中项
  activeQuickQueryIndex.value = '0'
  
  // 数据加载完成后，设置菜单高度
  await nextTick()
  setMenuMaxHeight()
}

/**
 * 处理快捷查询列表选择
 */
const handleQuickQuerySelect = (index: string) => {
  if (!props.quickQueryList) {
    return
  }

  const selected = quickQueryData.value.find((item, idx) => idx.toString() === index)
  if (selected) {
    activeQuickQueryIndex.value = index
    const config = props.quickQueryList
    const field = config.field

    // 更新查询参数
    if (selected.id === null || selected.id === undefined || selected.id === '') {
      // "（全部）"选项，删除该字段
      delete internalSearchParams.value[field]
    } else {
      // 设置查询字段值
      internalSearchParams.value[field] = selected.id
    }

    // 重置到第一页并刷新列表
    currentPage.value = 1
    getList()
  }
}

// 监听 quickQueryList 变化，重新初始化
watch(
  () => props.quickQueryList,
  () => {
    initQuickQueryList()
  },
  { immediate: true }
)

// ==================== ElMenu 高度处理 ====================
/** ElMenu 容器引用 */
const quickQueryMenuWrapperRef = ref<HTMLElement>()
/** ElMenu 组件引用 */
const quickQueryMenuRef = ref<InstanceType<typeof ElMenu>>()

/** 上次设置的高度，用于避免重复设置 */
let lastSetHeight = 0
/** 是否正在设置高度，用于防止死循环 */
let isSettingHeight = false

/**
 * 设置 ElMenu 的最大化高度
 */
const setMenuMaxHeight = async () => {
  if (!props.quickQueryList || !quickQueryMenuWrapperRef.value) {
    return
  }
  
  if (isSettingHeight) {
    return
  }

  isSettingHeight = true
  
  try {
    await nextTick()
    await nextTick() // 确保 DOM 完全渲染
    
    const wrapper = quickQueryMenuWrapperRef.value
    
    // 获取整个布局链的元素
    const baseGridWrapper = wrapper.closest('.base-grid-wrapper') as HTMLElement
    const contentArea = wrapper.closest('.base-grid-content-area') as HTMLElement
    const quickQueryList = wrapper.closest('.base-grid-quick-query-list') as HTMLElement
    
    // quickQueryList 本身就是 ElCard (DIV.el-card)
    const card = quickQueryList
    const cardBody = card?.querySelector('.el-card__body') as HTMLElement
    const queryBar = baseGridWrapper?.querySelector('.query-bar') as HTMLElement
    
    // 向上查找 ContentWrap（从 baseGridWrapper 向上查找）
    let contentWrap: HTMLElement | null = null
    let currentElement: HTMLElement | null = baseGridWrapper
    while (currentElement && !contentWrap) {
      contentWrap = currentElement.closest('.content-wrap') as HTMLElement
      if (!contentWrap && currentElement.parentElement) {
        currentElement = currentElement.parentElement as HTMLElement
      } else {
        break
      }
    }
    const contentWrapCardBody = contentWrap?.querySelector('.el-card__body') as HTMLElement
    
    if (!cardBody || !quickQueryList || !contentArea || !baseGridWrapper) {
      return
    }

    // 获取必要的高度信息
    const contentWrapCardBodyRect = contentWrapCardBody?.getBoundingClientRect()
    const baseGridWrapperRect = baseGridWrapper.getBoundingClientRect()
    const contentAreaRect = contentArea.getBoundingClientRect()
    const cardHeader = card.querySelector('.el-card__header') as HTMLElement
    const cardHeaderHeight = cardHeader ? cardHeader.getBoundingClientRect().height : 0
    const queryBarHeight = queryBar ? queryBar.getBoundingClientRect().height : 0
    
    // 计算可用高度
    // 优先使用 ContentWrap Card body 的高度（最准确）
    // 否则使用多种方法计算，取最大值以确保充分利用空间
    const windowHeight = window.innerHeight
    const FOOTER_HEIGHT = 50 // Footer 的标准高度
    
    let baseAvailableHeight = 0
    if (contentWrapCardBodyRect && contentWrapCardBodyRect.height > 0) {
      // 使用 ContentWrap Card body 的高度（最准确）
      baseAvailableHeight = contentWrapCardBodyRect.height - queryBarHeight
    } else {
      // 获取计算所需的位置信息
      const contentAreaTop = contentAreaRect.top
      
      // 使用两种不同的方法计算可用高度，以应对不同的布局情况
      const calculatedHeights = [
        // 方法1：基于 baseGridWrapper 实际高度计算（适用于 flex 布局）
        baseGridWrapperRect.height - queryBarHeight,
        // 方法2：基于窗口高度计算（适用于全屏布局，考虑 Footer）
        windowHeight - contentAreaTop - FOOTER_HEIGHT - queryBarHeight
      ]
      
      // 取两种方法的最大值，确保充分利用可用空间
      baseAvailableHeight = Math.max(...calculatedHeights)
      
      // 安全限制：确保不超过窗口实际可用高度
      const maxPossibleHeight = windowHeight - contentAreaTop - queryBarHeight
      baseAvailableHeight = Math.min(baseAvailableHeight, maxPossibleHeight)
    }
    
    // 减去 Card header 高度和底部间距（10px）
    const availableHeight = Math.max(0, baseAvailableHeight - cardHeaderHeight - 10 - 1)
    
    // 如果高度没有变化，不需要重新设置
    if (Math.abs(availableHeight - lastSetHeight) < 1) {
      return
    }
    
    // 查找 ElMenu 元素和其包装器
    const menuElement = wrapper.querySelector('.base-grid-quick-query-menu') as HTMLElement
    let menuWrapper = wrapper.querySelector('.base-grid-quick-query-menu-wrapper') as HTMLElement
    if (!menuWrapper && quickQueryMenuWrapperRef.value) {
      menuWrapper = quickQueryMenuWrapperRef.value as HTMLElement
    }
    if (!menuWrapper && menuElement?.parentElement) {
      menuWrapper = menuElement.parentElement as HTMLElement
    }
    
    if (menuElement && availableHeight > 0) {
      // 设置 Card body 的 padding 为 0，确保底部没有额外的 padding
      if (cardBody) {
        cardBody.style.setProperty('padding', '0', 'important')
        cardBody.style.setProperty('padding-bottom', '0', 'important')
      }
      
      // 设置 menuWrapper 的高度和样式
      if (menuWrapper) {
        menuWrapper.style.setProperty('height', `${availableHeight}px`, 'important')
        menuWrapper.style.setProperty('max-height', `${availableHeight}px`, 'important')
        menuWrapper.style.setProperty('min-height', `${availableHeight}px`, 'important')
        menuWrapper.style.setProperty('overflow', 'hidden', 'important')
        menuWrapper.style.setProperty('display', 'flex', 'important')
        menuWrapper.style.setProperty('flex-direction', 'column', 'important')
        menuWrapper.style.setProperty('flex', '1', 'important')
        menuWrapper.style.setProperty('box-sizing', 'border-box', 'important')
        menuWrapper.style.setProperty('margin-bottom', '10px', 'important')
        
        // 强制重新计算布局
        void menuWrapper.offsetHeight
      }
      
      // 设置 ElMenu 的高度和样式
      menuElement.style.setProperty('height', `${availableHeight}px`, 'important')
      menuElement.style.setProperty('max-height', `${availableHeight}px`, 'important')
      menuElement.style.setProperty('min-height', `${availableHeight}px`, 'important')
      menuElement.style.setProperty('overflow-y', 'auto', 'important')
      menuElement.style.setProperty('overflow-x', 'hidden', 'important')
      menuElement.style.setProperty('width', '100%', 'important')
      menuElement.style.setProperty('display', 'block', 'important')
      menuElement.style.setProperty('box-sizing', 'border-box', 'important')
      
      // 更新上次设置的高度
      lastSetHeight = availableHeight
    }
  } finally {
    // 延迟重置标志，避免频繁触发
    setTimeout(() => {
      isSettingHeight = false
    }, 100)
  }
}

// 监听窗口大小变化，重新计算高度
let resizeTimer: ReturnType<typeof setTimeout> | null = null

// 防抖函数（延迟更长，避免频繁触发）
const debouncedSetMenuMaxHeight = () => {
  if (resizeTimer) {
    clearTimeout(resizeTimer)
  }
  resizeTimer = setTimeout(() => {
    setMenuMaxHeight()
  }, 300) // 增加延迟时间
}

onMounted(() => {
  if (props.quickQueryList) {
    // 延迟执行，确保 DOM 完全渲染
    setTimeout(() => {
      setMenuMaxHeight()
    }, 200)
    
    // 监听窗口大小变化，重新计算高度
    window.addEventListener('resize', debouncedSetMenuMaxHeight)
  }
})

watch(
  () => props.quickQueryList,
  () => {
    if (props.quickQueryList) {
      setTimeout(() => {
        setMenuMaxHeight()
      }, 100)
    }
  }
)

// 监听 quickQueryData 变化，数据加载完成后重新设置高度
watch(
  () => quickQueryData.value,
  () => {
    if (props.quickQueryList && quickQueryData.value.length > 0) {
      setTimeout(() => {
        setMenuMaxHeight()
      }, 200)
    }
  }
)

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

/**
 * 处理刷新事件
 */
const handleRefresh = () => {
  showInfo() // 清空提示信息，显示就绪状态
  getList()
}
// ==================== 表格状态管理 ====================
const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const { pageSize, currentPage } = tableState
    const res = await props.fetchDataApi({
      page: unref(currentPage),
      limit: unref(pageSize),
      ...unref(internalSearchParams.value) // 使用查询条件参数
    })

    return {
      list: res.data || [],
      total: res.count || 0
    }
  },
  fetchDelApi: props.fetchDelApi
})

const { dataList, loading, total, pageSize, currentPage } = tableState
const { getList, getSelections } = tableMethods

const { showAction, nodeKey, reserveSelection } = props

// ==================== 工具函数 ====================
/**
 * 渲染操作按钮
 * @param options 操作按钮配置数组
 * @param row 当前行数据
 * @param col 列配置（可选）
 */
const renderActionButtons = (
  options: ActionOption[],
  row: any,
  col?: GridColumn
) => {
  return (
    <>
      {options.map((option, index) => {
        const { type, label, onClick, permission, ...buttonProps } = option

        // 默认按钮文字
        const buttonLabel = label || (type === 'edit' ? '修改' : type === 'delete' ? '删除' : '操作')
        // 默认按钮类型
        const buttonType = buttonProps.type || (type === 'delete' ? 'danger' : 'primary')

        // 处理点击事件
        const handleClick = () => {
          if (onClick) {
            onClick(row)
          } else if (type === 'edit' && col?.onEdit) {
            col.onEdit(row)
          } else if (type === 'delete' && col?.onDelete) {
            col.onDelete(row)
          } else if (type === 'delete' && props.fetchDelApi && tableMethods) {
            tableMethods.delList(true, [row[props.nodeKey]])
          }
        }

        return (
          <BaseButton
            key={index}
            type={buttonType}
            link
            size="small"
            onClick={handleClick}
            {...buttonProps}
          >
            {buttonLabel}
          </BaseButton>
        )
      })}
    </>
  )
}

// ==================== 列转换函数 ====================
/**
 * 将 GridColumn 配置转换为 TableColumn
 * @param columns 列配置数组
 * @returns TableColumn 数组
 */
const convertColumns = (columns: GridColumn[]): TableColumn[] => {
  return columns.map((col) => {
    // 基础列配置
    const baseColumn: TableColumn = {
      field: col.field,
      label: col.label,
      show: col.show !== false,
      width: col.width,
      minWidth: col.minWidth,
      align: col.align,
      fixed: col.fixed,
      // showConfig 属性：true=可在右上角配置显示/隐藏，false=不可配置，固定显示
      // 默认值为 true（可配置）
      showConfig: col.showConfig !== undefined ? col.showConfig : true
    }

    // 根据列类型进行特殊处理
    switch (col.type) {
      case 'selection':
        return {
          ...baseColumn,
          type: 'selection',
          // selection 列默认显示，但尊重用户设置的 show 值
          show: col.show !== false
        }

      case 'image':
        // 图片列：支持单张图片或图片列表，支持预览
        return {
          ...baseColumn,
          // 使用 baseColumn.show，已正确处理 col.show !== false
          slots: {
            default: (data: any) => {
              const row = data.row
              const imageField = col.imageField || col.field // 图片字段名
              const imageListField = col.imageListField || imageField // 图片列表字段名
              const imageHeight = col.imageHeight || '60px' // 图片显示高度

              /**
               * 标准化图片 URL，添加 OSS 处理参数
               * @param url 原始图片 URL
               * @returns 处理后的图片 URL
               */
              const normalizeImageUrl = (url: string) => {
                if (!url) return DEFAULT_IMAGE
                const [path] = url.split('?')
                return path ? `${path}?x-oss-process=image/resize,m_fixed,h_100` : DEFAULT_IMAGE
              }

              let imageUrl = DEFAULT_IMAGE
              let previewList: string[] = []

              // 处理图片列表
              if (Array.isArray(row[imageListField]) && row[imageListField].length > 0) {
                imageUrl = normalizeImageUrl(row[imageListField][0])
                // 生成预览列表（移除 OSS 参数）
                previewList = row[imageListField]
                  .map((img: string) => {
                    if (typeof img === 'string' && img.includes('?')) {
                      const [path] = img.split('?')
                      return path || img
                    }
                    return img
                  })
                  .filter(Boolean)
              } else if (row[imageField]) {
                // 处理单张图片
                imageUrl = normalizeImageUrl(row[imageField])
                previewList = [imageUrl]
              }

              const hasImage = imageUrl !== DEFAULT_IMAGE && previewList.length > 0

              /**
               * 图片加载失败处理：替换为默认图片
               */
              const handleError = (e: Event) => {
                const img = e.target as HTMLImageElement
                if (img && img.src !== DEFAULT_IMAGE) {
                  img.src = DEFAULT_IMAGE
                }
              }

              return (
                <div class="resource-image-name flex items-center">
                  <div>
                    <ElImage
                      src={imageUrl}
                      onError={handleError}
                      zoom-rate={1.2}
                      preview-src-list={hasImage ? previewList : []}
                      preview-teleported={true}
                      hide-on-click-modal={true}
                      initial-index={data.$index}
                      style={`height: ${imageHeight}; display: block`}
                      fit="cover"
                    />
                  </div>
                </div>
              )
            }
          }
        }

      case 'status':
        // 状态列：根据状态值映射显示文字
        return {
          ...baseColumn,
          // 使用 baseColumn.show，已正确处理 col.show !== false
          formatter: (row: any) => {
            // 优先使用自定义格式化函数
            if (col.formatter) {
              return col.formatter(row)
            }
            // 获取状态选项（支持函数或数组）
            let statusOptions: Array<{ label: string; value: any }> | undefined
            if (col.statusOptions) {
              statusOptions = typeof col.statusOptions === 'function' 
                ? col.statusOptions() 
                : col.statusOptions
            }
            // 构建状态映射表并返回对应文字
            if (statusOptions && Array.isArray(statusOptions)) {
              const statusMap = statusOptions.reduce(
                (acc, item) => {
                  acc[item.value] = item.label
                  return acc
                },
                {} as Record<any, string>
              )
              return statusMap[row[col.field]] || '未知'
            }
            return row[col.field]
          }
        }

      case 'action':
        // 操作列：渲染操作按钮（编辑、删除、自定义）
        return {
          ...baseColumn,
          // 使用 baseColumn.show，已正确处理 col.show !== false
          align: col.align || 'center',
          fixed: col.fixed || 'right',
          slots: {
            default: (data: any) => {
              // 优先使用自定义插槽
              if (col.actionSlots) {
                return col.actionSlots(data)
              }

              const row = data.row
              const options = col.actionOptions || []

              // 如果没有配置操作选项，使用默认的编辑和删除按钮
              if (options.length === 0) {
                const defaultOptions: ActionOption[] = []
                if (col.onEdit) {
                  defaultOptions.push({ type: 'edit', onClick: col.onEdit })
                }
                if (col.onDelete || props.fetchDelApi) {
                  defaultOptions.push({ type: 'delete', onClick: col.onDelete })
                }
                return renderActionButtons(defaultOptions, row, col)
              }

              return renderActionButtons(options, row, col)
            }
          }
        }

      case 'text':
      default:
        // 文本列：默认类型，支持自定义格式化
        return {
          ...baseColumn,
          show: true,
          formatter: col.formatter
        }
    }
  })
}

// ==================== 表格列配置 ====================
/**
 * 转换列配置，过滤掉 show: false 的列（这些列不会显示，也不会出现在列配置选项中）
 * @param columns 原始列配置
 * @param preserveShowState 保留现有列的 show 状态映射（用于列配置弹窗中的用户操作）
 * @returns 转换后的列配置数组（已过滤掉 show: false 的列）
 */
const convertAndFilterColumns = (
  columns: GridColumn[],
  preserveShowState?: Map<string, boolean>
): TableColumn[] => {
  // 先转换所有列
  const converted = convertColumns(columns)
  
  // 过滤掉 show: false 的列
  return converted.filter((col) => {
    // 如果原始配置中 show: false，完全过滤掉该列
    const originalCol = columns.find((c) => c.field === col.field)
    if (originalCol && originalCol.show === false) {
      return false
    }
    
    // 如果 preserveShowState 存在且包含该列，使用保留的 show 状态
    // 这样可以保留用户在列配置弹窗中的操作
    if (preserveShowState && preserveShowState.has(col.field)) {
      col.show = preserveShowState.get(col.field)!
    }
    
    return true
  })
}

/** 转换后的表格列配置（使用 reactive 确保响应式，与 Dish.vue 保持一致） */
const tableColumns = reactive<TableColumn[]>(convertAndFilterColumns(props.columns))

/**
 * 监听 props.columns 变化，同步更新 tableColumns
 * 注意：
 * 1. show: false 的列会被完全过滤掉，不会出现在列配置选项中
 * 2. 保留用户对 show 属性的修改（列配置弹窗中的显示/隐藏设置）
 */
watch(
  () => props.columns,
  (newColumns) => {
    // 创建现有列的字段映射，用于保留 show 属性（用户通过列配置弹窗修改的）
    const existingShowMap = new Map<string, boolean>()
    tableColumns.forEach((col) => {
      existingShowMap.set(col.field, col.show)
    })
    
    // 转换并过滤列，保留用户的 show 设置
    const newTableColumns = convertAndFilterColumns(newColumns, existingShowMap)
    
    // 清空并重新填充数组
    tableColumns.length = 0
    newTableColumns.forEach((newCol) => {
      tableColumns.push(newCol)
    })
  },
  { deep: false } // 只监听数组引用变化，不深度监听
)

// ==================== 暴露方法 ====================
defineExpose({
  getList, // 刷新列表
  getSelections, // 获取选中的行
  tableMethods, // 表格方法集合
  tableState, // 表格状态
  showInfo // 显示信息提示
})
</script>

<template>
  <div class="base-grid-wrapper">
    <!-- 查询条件区域 -->
    <QueryBar 
      v-if="props.searchConditions && props.searchConditions.length > 0"
      :conditions="props.searchConditions"
      @search="handleSearch"
      @reset="handleReset"
    />

    <!-- 内容区域：左侧快捷查询列表 + 右侧表格 -->
    <div v-if="props.quickQueryList" class="base-grid-content-area">
    <!-- 左侧快捷查询列表 -->
    <ElCard class="base-grid-quick-query-list" :header="props.quickQueryList.title" shadow="never" :body-style="{ padding: '0', paddingBottom: '0' }">
      <div ref="quickQueryMenuWrapperRef" class="base-grid-quick-query-menu-wrapper">
        <ElMenu
          ref="quickQueryMenuRef"
          class="base-grid-quick-query-menu"
          shadow="never"
          :default-active="activeQuickQueryIndex"
          @select="handleQuickQuerySelect"
        >
          <ElMenuItem
            v-for="(item, index) in quickQueryData"
            :key="item.id ?? index"
            :index="index.toString()"
          >
            {{ item.label }}
          </ElMenuItem>
        </ElMenu>
      </div>
    </ElCard>
    <!-- 右侧表格 -->
    <div class="base-grid-right-table">
      <Table
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :show-action="showAction"
        :columns="tableColumns"
        :node-key="nodeKey"
        :data="dataList"
        :loading="loading"
        :pagination="{
          total
        }"
        :reserve-selection="reserveSelection"
        @register="tableRegister"
        @refresh="handleRefresh"
      >
        <template #toolbar>
          <div class="base-grid-toolbar-wrapper">
            <div class="base-grid-toolbar-left">
              <template v-if="props.toolbarButtons && props.toolbarButtons.length > 0">
                <template v-for="btn in props.toolbarButtons" :key="btn.stype">
                  <ButtonPre :stype="btn.stype" @click="btn.onClick">
                    <template v-if="btn.label">{{ btn.label }}</template>
                  </ButtonPre>
                </template>
              </template>
              <slot name="toolbar-left"></slot>
            </div>

            <div class="base-grid-toolbar-info">
              <PrompInfo ref="prompInfoRef" />
            </div>
          </div>
          <slot name="toolbar"></slot>
        </template>
      </Table>
    </div>
  </div>
  <!-- 无快捷查询列表时，直接显示表格 -->
  <Table
    v-else
    v-model:current-page="currentPage"
    v-model:page-size="pageSize"
    :show-action="showAction"
    :columns="tableColumns"
    :node-key="nodeKey"
    :data="dataList"
    :loading="loading"
    :pagination="{
      total
    }"
    :reserve-selection="reserveSelection"
    @register="tableRegister"
    @refresh="handleRefresh"
  >
    <template #toolbar>
      <div class="base-grid-toolbar-wrapper">
        <div class="base-grid-toolbar-left">
          <template v-if="props.toolbarButtons && props.toolbarButtons.length > 0">
            <template v-for="btn in props.toolbarButtons" :key="btn.stype">
              <ButtonPre :stype="btn.stype" @click="btn.onClick">
                <template v-if="btn.label">{{ btn.label }}</template>
              </ButtonPre>
            </template>
          </template>
          <slot name="toolbar-left"></slot>
        </div>

        <div class="base-grid-toolbar-info">
          <PrompInfo ref="prompInfoRef" />
        </div>
      </div>
      <slot name="toolbar"></slot>
    </template>
  </Table>
  </div>
</template>

<style scoped>
/* 确保 ContentWrap 内部的布局正确 */
:deep(.content-wrap) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}

:deep(.content-wrap .el-card) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}

:deep(.content-wrap .el-card__body) {
  flex: 1 !important;
  display: flex !important;
  flex-direction: column !important;
  min-height: 0 !important;
  overflow: hidden !important;
}

:deep(.content-wrap > div) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
}

/* BaseGrid 根容器 */
.base-grid-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  /* 确保填充父容器 */
}

/* 内容区域：左侧快捷查询列表 + 右侧表格 */
.base-grid-content-area {
  display: flex;
  flex: 1;
  min-height: 0; /* 允许 flex 子元素收缩 */
  overflow: hidden; /* 防止产生纵向滚动 */
  align-items: stretch; /* 确保子元素高度一致 */
  height: 100%; /* 确保填充父容器 */
}

/* 左侧快捷查询列表 */
.base-grid-quick-query-list {
  width: 160px;
  margin-right: 10px;
  flex-shrink: 0;
  display: flex !important;
  flex-direction: column !important;
  height: 100% !important;
  min-height: 0; /* 允许 flex 子元素收缩 */
  align-self: stretch; /* 确保高度填充 */
}

.base-grid-quick-query-list :deep(.el-card) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important; /* 移除所有 padding */
}

.base-grid-quick-query-list :deep(.el-card__header) {
  padding: 15px 20px !important; /* 只保留 header 的 padding */
  margin-bottom: 0 !important;
}

/* ElCard 内部布局 */
.base-grid-quick-query-list :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0 !important; /* 移除所有 padding */
  padding-bottom: 0 !important; /* 确保底部没有额外的 padding */
  overflow: hidden;
  /* 使用 flex: 1 自动填充，而不是固定 height: 100% */
  /* 确保 Card body 填充 ElCard 的剩余高度（总高度 - header 高度） */
}

/* 菜单包装器 */
.base-grid-quick-query-menu-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-bottom: 10px !important; /* 与底部版权信息保持 10px 间距 */
  /* 确保 wrapper 填充父容器高度 */
  height: 100%;
  box-sizing: border-box;
}

/* ElMenu - 高度通过 JavaScript 动态设置，确保固定最大化高度 */
/* menuElement 本身就是 ul.el-menu，所以直接设置 */
.base-grid-quick-query-menu {
  width: 100% !important;
  box-sizing: border-box !important;
  /* 高度通过 JavaScript 动态设置，使用内联样式优先级最高 */
  /* 不设置 height，让 JavaScript 完全控制 */
}

/* 右侧表格 */
.base-grid-right-table {
  flex: 1;
  overflow-x: auto;
}

/* 图片列样式 */
.resource-image-name {
  display: flex;
  align-items: center;
}

/* 让 Table 组件的左侧 div 占据全部可用空间 */
:deep(.flex.justify-between > div:first-child) {
  flex: 1;
  min-width: 0;
  display: flex;
}

/* 工具栏容器 */
.base-grid-toolbar-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 10px;
  margin-right: 10px; /* 与右侧刷新按钮保持 10px 间距 */
  min-width: 0;
}

/* 工具栏左侧按钮区域 */
.base-grid-toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px; /* 按钮之间间距 10px */
  flex-shrink: 0;
}

/* 移除 ButtonPre 按钮的默认 margin，确保间距由 gap 控制 */
.base-grid-toolbar-left :deep(.my-button) {
  margin: 0;
}

/* 工具栏中间信息显示区域 */
.base-grid-toolbar-info {
  flex: 1; /* 占据剩余空间 */
  display: flex;
  align-items: center;
  min-width: 0;
  overflow: hidden;
}
</style>


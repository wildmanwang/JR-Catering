<script setup lang="tsx">
import { computed, ref, toRefs, watch, nextTick } from 'vue'
import { ElUpload, UploadProps, ElIcon, ElImage, ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/modules/auth'
import {
  processImageList,
  normalizeImageUrl,
  isDeletedImage,
  removeQueryParams,
  cleanImageArray,
  ImageQuerySuffix,
  getImageUrlWithSuffix
} from '@/utils/imageList'

// ==================== Props 定义 ====================
interface Props {
  /** 图片数据数组（用于存储和提交） */
  modelValue?: any[]
  /** 是否禁用（查看模式） */
  disabled?: boolean
  /** 最大上传数量 */
  limit?: number
  /** 上传接口地址 */
  action?: string
  /** 上传时的额外数据 */
  data?: Record<string, any>
  /** 上传时的请求头 */
  headers?: Record<string, string>
  /** 图片尺寸：normal（100px*100px，默认）或 small（60px*60px） */
  size?: 'normal' | 'small'
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  disabled: false,
  limit: 10,
  action: '/api/vadmin/system/upload/image/to/local',
  data: () => ({ path: 'system' }),
  headers: () => ({}),
  size: 'normal'
})

// ==================== Emits 定义 ====================
const emit = defineEmits<{
  'update:modelValue': [value: any[]]
}>()

// ==================== Store ====================
const authStore = useAuthStore()
const token = computed(() => authStore.getToken)

// ==================== 计算属性 ====================
/** 当前图片数据 */
const imageData = computed({
  get: () => props.modelValue || [],
  set: (val) => emit('update:modelValue', val)
})

// 解构 props 以便在模板中直接使用（使用 toRefs 保持响应性）
const { disabled, action, data, limit, size } = toRefs(props)

// ==================== 内部显示数据（自动维护）====================
/** 显示用的图片数组（组件内部自动维护） */
const imageDisplayData = ref<any[]>([])

/**
 * 根据 modelValue 生成 displayValue
 * 处理逻辑：
 * 1. 如果是数组格式（新上传的图片），使用预览 URL
 * 2. 如果是字符串格式，移除操作标记（?original、?add 等），只保留路径用于显示
 * 3. 标记为 ?delete 的图片不显示（已删除）
 * 
 * 返回格式：{ display: string, key: string, originalIndex: number }
 * - display: 用于显示的图片 URL
 * - key: 用于 Vue key 的唯一标识符（稳定的，不会因为删除而变化）
 * - originalIndex: 在 imageData 中的原始索引
 */
const generateDisplayData = (imageData: any[]): Array<{ display: string; key: string; originalIndex: number }> => {
  if (!imageData || !Array.isArray(imageData)) {
    return []
  }

  const result: Array<{ display: string; key: string; originalIndex: number }> = []
  
  imageData.forEach((item: any, originalIndex: number) => {
    // 过滤掉标记为删除的图片
    if (typeof item === 'string' && isDeletedImage(item)) {
      return
    }
    
    let display: string
    let key: string
    
    // 如果是数组格式（新上传的图片），使用预览 URL（第一个元素）
    if (Array.isArray(item) && item.length > 0) {
      display = item[0]
      // 使用文件对象的 name 或预览 URL 作为 key（更稳定）
      key = item[2] || item[0] || `new-${originalIndex}`
    } else if (typeof item === 'string') {
      // 如果是字符串格式，移除操作标记，只保留路径
      display = removeQueryParams(item)
      // 使用图片路径（去掉标记）作为 key，这样删除其他图片时不会影响当前图片的 key
      key = display
    } else {
      display = item
      key = `item-${originalIndex}`
    }
    
    result.push({ display, key, originalIndex })
  })
  
  return result
}

/**
 * 初始化显示数据
 */
const initDisplayData = () => {
  imageDisplayData.value = generateDisplayData(imageData.value)
}

// 初始化显示数据
initDisplayData()

// 内部更新标志，用于区分是组件内部操作还是外部数据变化
const isInternalUpdate = ref(false)

// 规范化标志，用于区分是规范化操作还是用户操作
const isNormalizing = ref(false)

/**
 * 规范化输入的图片数据格式
 * 处理逻辑：
 * 1. 确保输入数据是数组格式（如果不是数组，返回空数组）
 * 2. 检查数据格式：如果第一个元素包含 '-' 且以数字开头（如 "10-path"），说明是未处理的数据库格式
 * 3. 如果是未处理格式，排序并提取路径
 * 4. 添加 ?original 标记（如果还没有标记）
 * 
 * @param imageData 输入的图片数据（可能是数组、null、undefined 或其他类型）
 * @returns 规范化后的图片数据数组
 */
const normalizeInputImageData = (imageData: any): any[] => {
  // 确保输入数据是数组格式（封装到组件内部处理）
  if (!imageData || !Array.isArray(imageData)) {
    return []
  }
  
  if (imageData.length === 0) {
    return []
  }

  // 检查数据格式：如果第一个元素包含 '-' 且以数字开头，说明是未处理的数据库格式
  const needsProcessing = typeof imageData[0] === 'string' && 
    imageData[0].includes('-') &&
    /^\d+-/.test(imageData[0])

  if (needsProcessing) {
    // 使用 processImageList 处理排序前缀并排序
    const processedImages = processImageList(imageData as string[])
    
    // 标记为 original（如果还没有标记）
    return processedImages.map((item: string) => {
      return normalizeImageUrl(item)
    }).filter(Boolean)
  } else {
    // 数据已经处理过，只需要确保没有标记的项添加 ?original 标记
    return imageData.map((item: any) => {
      if (typeof item === 'string' && item.length) {
        return normalizeImageUrl(item)
      }
      return item
    }).filter(Boolean)
  }
}

// 监听 modelValue 变化，自动更新显示数据
// 使用浅层监听，只监听数组引用变化，避免深度监听导致的性能问题
watch(
  () => props.modelValue,
  (newValue, oldValue) => {
    // 如果是组件内部操作导致的更新，跳过（因为内部操作已经更新了显示数据）
    if (isInternalUpdate.value) {
      isInternalUpdate.value = false
      return
    }

    // 如果是规范化操作导致的更新，跳过
    if (isNormalizing.value) {
      return
    }

    // 如果引用相同，跳过更新（避免不必要的重新计算）
    if (newValue === oldValue) {
      return
    }

    // 外部数据变化，先规范化数据格式，然后更新显示数据
    // normalizeInputImageData 内部已处理非数组情况（返回空数组），直接调用即可
    const normalizedData = normalizeInputImageData(newValue)
    
    // 如果数据格式发生了变化，更新 modelValue（触发父组件更新）
    const isArrayValue = newValue && Array.isArray(newValue)
    const dataChanged = !isArrayValue || 
        normalizedData.length !== newValue.length || 
        normalizedData.some((item, index) => item !== newValue[index])
    
    if (dataChanged) {
      // 设置规范化标志，避免循环更新
      isNormalizing.value = true
      isInternalUpdate.value = true
      // 更新 modelValue，这会触发父组件更新
      imageData.value = normalizedData
      // 等待 nextTick 确保更新完成
      nextTick(() => {
        isNormalizing.value = false
        isInternalUpdate.value = false
      })
      // 更新显示数据（使用规范化后的数据）
      imageDisplayData.value = generateDisplayData(normalizedData)
    } else {
      // 数据格式没有变化，直接更新显示数据
      imageDisplayData.value = generateDisplayData(newValue)
    }
  },
  { immediate: false }
)

// ==================== 上传前验证 ====================
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

// ==================== 文件变化处理 ====================
const handleFileChange: UploadProps['onChange'] = (file) => {
  if (file.raw) {
    const exists = imageData.value.some((item: any) => {
      if (Array.isArray(item)) {
        return item[2] === file.name
      }
      return false
    })
    if (!exists) {
      const previewUrl = URL.createObjectURL(file.raw)
      // 更新图片数据（添加新上传的图片）
      const newImageData = [...imageData.value, [previewUrl, 'add', file.name, file]]
      isInternalUpdate.value = true
      imageData.value = newImageData
      // 自动更新显示数据
      imageDisplayData.value = generateDisplayData(newImageData)
    }
  }
}

// ==================== 索引映射函数 ====================
/**
 * 将 imageDisplayData 的索引映射到 imageData 的索引
 * 因为 imageDisplayData 过滤掉了 ?delete 标记的图片，所以索引可能不对齐
 * 
 * @param displayIndex imageDisplayData 的索引
 * @returns imageData 的索引，如果找不到则返回 -1
 */
const getImageDataIndex = (displayIndex: number): number => {
  if (displayIndex < 0 || !imageDisplayData.value || !Array.isArray(imageDisplayData.value)) {
    return -1
  }
  
  const displayItem = imageDisplayData.value[displayIndex]
  if (displayItem && typeof displayItem === 'object' && 'originalIndex' in displayItem) {
    return displayItem.originalIndex
  }
  
  return -1
}

// ==================== 删除图片 ====================
const handleRemoveImage = (index: number) => {
  // index 是 imageDisplayData 的索引，需要映射到 imageData 的索引
  const imageDataIndex = getImageDataIndex(index)

  if (imageDataIndex === -1) {
    return
  }

  if (Array.isArray(imageData.value[imageDataIndex])) {
    // 如果是新上传的图片（数组格式），直接删除
    const newImageData = [...imageData.value]
    newImageData.splice(imageDataIndex, 1)
    isInternalUpdate.value = true
    imageData.value = newImageData
    // 自动更新显示数据
    imageDisplayData.value = generateDisplayData(newImageData)
  } else {
    // 如果是已存在的图片（字符串格式）
    const newImageData = [...imageData.value]
    const currentItem = newImageData[imageDataIndex]
    if (typeof currentItem === 'string') {
      // 检查图片标记
      if (currentItem.includes(`?${ImageQuerySuffix.ADD}`)) {
        // 如果是 ?add 标记的图片（后台不存在），直接从数组中删除
        newImageData.splice(imageDataIndex, 1)
      } else {
        // 如果是 ?original 标记的图片（后台已存在），标记为删除
        const path = removeQueryParams(currentItem)
        newImageData[imageDataIndex] = getImageUrlWithSuffix(path, ImageQuerySuffix.DELETE)
      }
      isInternalUpdate.value = true
      imageData.value = newImageData
      // 自动更新显示数据（删除标记的图片会被过滤掉，不显示）
      imageDisplayData.value = generateDisplayData(newImageData)
    }
  }
}

// ==================== 拖拽排序 ====================
const dragIndex = ref(-1)
const dragOverIndex = ref(-1)

const handleDragStart = (index: number, event: DragEvent) => {
  if (props.disabled) return
  dragIndex.value = index
  event.dataTransfer!.effectAllowed = 'move'
  event.dataTransfer!.setData('text/plain', index.toString())
  setTimeout(() => {
    ;(event.target as HTMLElement).classList.add('dragging')
  }, 0)
}

const handleDragOver = (event: DragEvent) => {
  if (props.disabled) return
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'move'
}

const handleDragEnter = (index: number, event: DragEvent) => {
  if (props.disabled) return
  event.preventDefault()
  dragOverIndex.value = index
}

const handleDragLeave = (event: DragEvent) => {
  if (props.disabled) return
  if (!(event.currentTarget as HTMLElement).contains(event.relatedTarget as HTMLElement)) {
    dragOverIndex.value = -1
  }
}

const handleDrop = (targetIndex: number, event: DragEvent) => {
  if (props.disabled) return
  event.preventDefault()
  const sourceDisplayIndex = parseInt(event.dataTransfer!.getData('text/plain'))
  
  // sourceDisplayIndex 和 targetIndex 都是 imageDisplayData 的索引
  // 需要映射到 imageData 的索引
  const sourceImageDataIndex = getImageDataIndex(sourceDisplayIndex)
  const targetImageDataIndex = getImageDataIndex(targetIndex)
  
  if (
    sourceImageDataIndex !== -1 &&
    targetImageDataIndex !== -1 &&
    sourceImageDataIndex !== targetImageDataIndex &&
    sourceDisplayIndex >= 0 &&
    targetIndex >= 0
  ) {
    // 更新图片数据（使用映射后的索引）
    const imagesData = [...imageData.value]
    const [movedItem] = imagesData.splice(sourceImageDataIndex, 1)
    imagesData.splice(targetImageDataIndex, 0, movedItem)
    isInternalUpdate.value = true
    imageData.value = imagesData
    // 自动更新显示数据
    imageDisplayData.value = generateDisplayData(imagesData)
  }
  dragIndex.value = -1
  dragOverIndex.value = -1
}

const handleDragEnd = () => {
  if (props.disabled) return
  dragIndex.value = -1
  dragOverIndex.value = -1
  const draggingElements = document.querySelectorAll('.dragging')
  draggingElements.forEach((el) => {
    el.classList.remove('dragging')
  })
}

// ==================== 生成预览列表 ====================
/**
 * 生成预览列表：过滤掉删除标记和 OSS 参数
 */
const generatePreviewList = (): string[] => {
  if (!imageDisplayData.value || !Array.isArray(imageDisplayData.value)) {
    return []
  }
  return imageDisplayData.value
    .map((item: any) => {
      // 如果是新格式（对象），使用 display 属性
      if (typeof item === 'object' && item !== null && 'display' in item) {
        return item.display
      }
      // 兼容旧格式（字符串）
      return typeof item === 'string' ? item : ''
    })
    .filter((img: string) => img && !isDeletedImage(img))
    .map((img: string) => {
      // 移除 OSS 参数，使用原始图片进行预览
      return removeQueryParams(img)
    })
    .filter(Boolean)
}

const previewList = computed(() => generatePreviewList())

// ==================== 图片加载失败处理 ====================
const handleError = (e: Event) => {
  const img = e.target as HTMLImageElement
  if (img && img.src) {
    // 图片加载失败时的处理逻辑
  }
}

// ==================== 计算上传组件是否显示 ====================
const showUploader = computed(() => {
  const displayLength = imageDisplayData.value ? imageDisplayData.value.length : 0
  return !disabled.value && displayLength < limit.value
})

// ==================== 合并请求头 ====================
const uploadHeaders = computed(() => {
  return {
    Authorization: token.value,
    ...props.headers
  }
})

// ==================== 上传文件 ====================
/**
 * 上传文件到服务器
 * @param fileForm FormData 对象，包含文件和额外数据
 * @returns 上传结果
 */
const uploadFile = async (
  fileForm: FormData
): Promise<{ success: boolean; message: string; data?: any }> => {
  try {
    const res = await fetch(props.action, {
      method: 'POST',
      body: fileForm,
      headers: {
        Authorization: token.value || '',
        ...props.headers
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

// ==================== 上传待上传的图片 ====================
/**
 * 上传待上传的图片
 * 检查图片数据中是否有数组格式的项（未上传的图片），如果有则上传
 * 上传成功后，将返回的图片地址转为指定格式后更新图片列表
 *
 * @returns Promise<void> 如果上传失败会抛出错误
 * @throws {Error} 上传失败时抛出错误
 */
const uploadPendingImages = async (): Promise<void> => {
  if (!imageData.value || !Array.isArray(imageData.value)) {
    return
  }

  const newImageData = [...imageData.value]

  for (let index = 0; index < newImageData.length; index++) {
    const fileData = newImageData[index]

    // 如果是数组格式（包含文件对象），说明是未上传的图片，需要上传
    if (Array.isArray(fileData) && fileData.length >= 4) {
      const fileForm = new FormData()
      fileForm.append('file', fileData[3].raw)

      // 添加额外数据
      Object.keys(props.data).forEach((key) => {
        fileForm.append(key, props.data[key])
      })

      const res = await uploadFile(fileForm)
      if (!res.success) {
        throw new Error(`图片上传错误：${res.message}`)
      }

      // 转换为字符串格式：路径 + 操作类型（add/update/delete）
      const operationType = (fileData[1] as ImageQuerySuffix) || ImageQuerySuffix.ADD
      const remotePath = res.data.data.remote_path
      newImageData[index] = getImageUrlWithSuffix(remotePath, operationType)
    }
  }

  // 更新数据
  isInternalUpdate.value = true
  imageData.value = newImageData
  // 自动更新显示数据
  imageDisplayData.value = generateDisplayData(newImageData)
}

// ==================== 图片路径规范化（组件内部实现）====================
/**
 * 规范化图片路径（用于提交数据）
 * 处理逻辑：
 * 1. 移除查询参数（?后面的部分）
 * 2. 添加 ?original 后缀
 * 3. 过滤空值
 * @param img 图片路径字符串
 * @returns 规范化后的图片路径
 */
const normalizeImagePath = (img: string): string => {
  return normalizeImageUrl(img)
}

/**
 * 获取规范化后的图片数组（用于提交数据）
 * 处理逻辑：
 * 1. 过滤掉标记为删除的图片（?delete）
 * 2. 规范化每个图片路径（移除查询参数，添加 ?original）
 * 3. 过滤空值
 * @param images 图片数据数组，如果不传则使用组件内部的 modelValue
 * @returns 规范化后的图片路径数组
 */
const getNormalizedImages = (images?: any[]): string[] => {
  const targetImages = images !== undefined ? images : imageData.value
  
  if (!targetImages || !Array.isArray(targetImages)) {
    return []
  }

  // 先过滤掉数组格式的项（未上传的图片，应该先上传）
  const stringItems = targetImages.filter((item: any) => {
    return typeof item === 'string' && !Array.isArray(item)
  }) as string[]
  
  // 使用 cleanImageArray 过滤删除标记并清理查询参数
  const cleanedItems = cleanImageArray(stringItems, {
    removeDeleted: true,
    removeQueryParams: false // 先不移除查询参数，后面统一规范化
  })
  
  // 规范化每个图片路径（添加 ?original）
  return cleanedItems.map((item: string) => normalizeImagePath(item)).filter(Boolean)
}

// ==================== 暴露方法 ====================
defineExpose({
  uploadPendingImages,
  getNormalizedImages
})
</script>

<template>
  <div :class="['image-container', `image-container-${size}`]">
    <template v-for="(item, index) in imageDisplayData" :key="item.key">
      <div
        v-if="item.display && !isDeletedImage(item.display)"
        :class="[
          `image-group-${size}`,
          !disabled && dragIndex === index ? 'dragging' : '',
          !disabled && dragOverIndex === index ? 'drag-over' : ''
        ]"
        :draggable="!disabled"
        @dragstart="handleDragStart(index, $event)"
        @dragover="handleDragOver"
        @dragenter="handleDragEnter(index, $event)"
        @dragleave="handleDragLeave"
        @drop="handleDrop(index, $event)"
        @dragend="handleDragEnd"
      >
        <ElImage
          :src="item.display"
          :class="`image-item-${size}`"
          @error="handleError"
          :zoom-rate="1.2"
          :preview-src-list="previewList.length > 0 ? previewList : []"
          preview-teleported
          hide-on-click-modal
          :initial-index="index"
          fit="cover"
          style="width: 100%; height: 100%"
        />
        <div v-if="!disabled" :class="`remove-btn-${size}`" @click.stop="handleRemoveImage(index)"> x </div>
      </div>
    </template>
    <div v-if="showUploader" :class="`image-group-uploader-${size}`">
      <ElUpload
        :action="action.value"
        :data="data.value"
        :show-file-list="false"
        :multiple="true"
        :auto-upload="false"
        :before-upload="beforeImageUpload"
        @change="handleFileChange"
        accept="image/jpeg,image/gif,image/png"
        name="file"
        drag
        :headers="uploadHeaders"
        :limit="limit.value"
      >
        <div :class="`upload-content-wrapper-${size}`">
          <ElIcon :class="`el-icon--upload-${size}`"><UploadFilled /></ElIcon>
          <div :class="`upload-text-${size}`">{{ size === 'small' ? '拖拽或点击' : '拖拽文件到此或点击上传' }}</div>
        </div>
      </ElUpload>
    </div>
  </div>
</template>

<style lang="less" scoped>
.image-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0;
}

// ==================== normal 尺寸（默认，100px*100px）====================
.image-group-normal {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0;
  // 防止拖拽时文本被选中，但不影响开发者工具选择
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  // 确保指针事件正常，不影响开发者工具
  pointer-events: auto;
}

.image-item-normal {
  width: 100%;
  height: 100%;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
  cursor: pointer;
}

.image-item-normal:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-group-normal :deep(.el-image) {
  width: 100%;
  height: 100%;
  border-radius: 6px;
}

.image-group-normal :deep(.el-image__inner) {
  border-radius: 6px;
  object-fit: cover;
}

.remove-btn-normal {
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

.image-group-normal:hover .remove-btn-normal {
  opacity: 1;
}

.image-group-uploader-normal {
  width: 180px;
  height: 100px;
  flex-shrink: 0;
}

.image-group-uploader-normal :deep(.el-upload) {
  border: 2px dashed #c0c4cc;
  width: 100% !important;
  height: 100px !important;
  margin: 0 !important;
  padding: 0 !important;
  border-radius: 6px;
  box-sizing: border-box !important;
  color: #606266; // 设置默认文字颜色
}

.image-group-uploader-normal :deep(.el-upload:hover) {
  border-color: #409eff;
  background: #f0f7ff;
  color: #409eff;
}

.image-group-uploader-normal :deep(.el-upload-dragger) {
  width: 100% !important;
  height: 100% !important;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 0 !important;
  margin: 0 !important;
  box-sizing: border-box !important;
}

// 上传内容包装器：确保上传图标和文字居中显示
.upload-content-wrapper-normal {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  overflow: visible;
  position: relative;
  gap: 0;
}

.el-icon--upload-normal {
  width: 54px;
  height: 54px;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  flex-shrink: 0;
  overflow: visible !important;
  position: relative;
}

.el-icon--upload-normal :deep(svg) {
  width: 54px !important;
  height: 54px !important;
  min-width: 54px !important;
  min-height: 54px !important;
  max-width: 54px !important;
  max-height: 54px !important;
  margin: 0 !important;
  padding: 0 !important;
  display: block !important;
  box-sizing: border-box !important;
  overflow: visible !important;
  position: static !important;
}

// 覆盖 SVG 元素上可能存在的固定高度属性
.el-icon--upload-normal :deep(svg[height]),
.el-icon--upload-normal :deep(svg[height="67"]),
.el-icon--upload-normal :deep(svg[height="67px"]) {
  height: 54px !important;
  max-height: 54px !important;
  width: 54px !important;
  max-width: 54px !important;
}

.upload-text-normal {
  font-size: 12px;
  margin-top: 4px;
  margin-bottom: 0;
  text-align: center;
  line-height: 1.2;
  padding: 0;
  flex-shrink: 0;
}

// ==================== small 尺寸（60px*60px，参考 ImportGrid）====================
.image-container-small {
  gap: 8px;
}

.image-group-small {
  position: relative;
  width: 60px;
  height: 60px;
  margin: 0;
  cursor: move;
  // 防止拖拽时文本被选中，但不影响开发者工具选择
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  // 确保指针事件正常，不影响开发者工具
  pointer-events: auto;
}

.image-item-small {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
  cursor: pointer;
}

.image-item-small:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-group-small :deep(.el-image) {
  width: 100%;
  height: 100%;
  border-radius: 4px;
}

.image-group-small :deep(.el-image__inner) {
  border-radius: 4px;
  object-fit: cover;
}

.remove-btn-small {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
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
  z-index: 100;
}

.image-group-small:hover .remove-btn-small {
  opacity: 1;
}

.image-group-small.dragging {
  opacity: 0.5;
  border-color: #409eff;
  transform: scale(0.95);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  cursor: grabbing;
  z-index: 1000;
}

.image-group-small.drag-over {
  transform: scale(1.15);
  border: 2px solid #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  z-index: 10;
  transition: all 0.2s ease;
}

.image-group-uploader-small {
  width: 60px;
  height: 60px;
  flex-shrink: 0;
  box-sizing: border-box;
  overflow: hidden;
  
  // 修复 ElUpload 组件自动生成的中间层 div（没有 class 的包装元素）
  > div {
    width: 100% !important;
    height: 100% !important;
    min-width: 100% !important;
    min-height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
    display: block !important;
  }
}

.image-group-uploader-small :deep(.el-upload) {
  border: 2px dashed #c0c4cc;
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  border-radius: 4px;
  box-sizing: border-box !important;
  min-width: 100% !important;
  min-height: 100% !important;
  max-width: 100% !important;
  max-height: 100% !important;
}

.image-group-uploader-small :deep(.el-upload:hover) {
  border-color: #409eff;
  background: #f0f7ff;
  color: #409eff;
}

.image-group-uploader-small :deep(.el-upload-dragger) {
  width: 100% !important;
  height: 100% !important;
  min-width: 100% !important;
  min-height: 100% !important;
  max-width: 100% !important;
  max-height: 100% !important;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 0 !important;
  margin: 0 !important;
  box-sizing: border-box !important;
}

// 上传内容包装器：确保上传图标和文字居中显示
.upload-content-wrapper-small {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  overflow: visible;
  position: relative;
  gap: 0;
}

.el-icon--upload-small {
  width: 24px;
  height: 24px;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  flex-shrink: 0;
  overflow: visible !important;
  position: relative;
}

.el-icon--upload-small :deep(svg) {
  width: 24px !important;
  height: 24px !important;
  min-width: 24px !important;
  min-height: 24px !important;
  max-width: 24px !important;
  max-height: 24px !important;
  margin: 0 !important;
  padding: 0 !important;
  display: block !important;
  box-sizing: border-box !important;
  overflow: visible !important;
  position: static !important;
}

// 覆盖 SVG 元素上可能存在的固定高度属性
.el-icon--upload-small :deep(svg[height]),
.el-icon--upload-small :deep(svg[height="67"]),
.el-icon--upload-small :deep(svg[height="67px"]) {
  height: 24px !important;
  max-height: 24px !important;
  width: 24px !important;
  max-width: 24px !important;
}

.upload-text-small {
  font-size: 10px;
  margin-top: 4px;
  margin-bottom: 0;
  text-align: center;
  line-height: 1.2;
  padding: 0;
  flex-shrink: 0;
}

// ==================== 通用样式（兼容旧代码，默认使用 normal 尺寸）====================
// 注意：这些样式仅作为后备，实际应该使用特定尺寸的类名
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

.image-group-uploader {
  width: 180px;
  height: 100px;
  flex-shrink: 0;
}

.image-group-uploader :deep(.el-upload) {
  border: 2px dashed #c0c4cc;
  width: 100% !important;
  height: 100px !important;
  margin: 0 !important;
  border-radius: 6px;
}

.image-group-uploader :deep(.el-upload:hover) {
  border-color: #409eff;
  background: #f0f7ff;
  color: #409eff;
}

.image-group-uploader :deep(.el-upload-dragger) {
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

// 拖拽和悬停效果（通用，但特定尺寸的样式会覆盖）
.image-group-normal.dragging,
.image-group-small.dragging {
  opacity: 0.5;
  border-color: #409eff;
  transform: scale(0.95);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  cursor: grabbing;
  z-index: 1000;
}

.image-group-normal.drag-over,
.image-group-small.drag-over {
  transform: scale(1.15);
  border: 2px solid #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  transform: scale(1.05);
  z-index: 10;
  transition: all 0.2s ease;
}
</style>

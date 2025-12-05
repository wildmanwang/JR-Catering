<script setup lang="tsx">
import { PropType, computed, ref, unref, reactive, watch } from 'vue'
import { Form, FormSchema } from '@/components/Form'
import { useValidator } from '@/hooks/web/useValidator'
import { useForm } from '@/hooks/web/useForm'
import { getKitchenListApi } from '@/api/vadmin/product/kitchen'
import { ElMessage, ElUpload, UploadProps, ElIcon } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/modules/auth'

const { required } = useValidator()
const authStore = useAuthStore()

const props = defineProps({
  dialogVisible: {
    type: Boolean,
    required: true
  },
  currentRow: {
    type: Object as PropType<any>,
    default: () => null
  },
  dishStatusOptions: {
    type: Array as PropType<Array<{ label: string, value: number }>>,
    default: () => []
  }
})

const token = computed(() => authStore.getToken)

const formSchema = reactive<FormSchema[]>([
  {
    field: 'name_unique',
    label: '名称',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'name_display',
    label: '显示名称',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'name_english',
    label: '英文名称',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'kitchen_id',
    label: '厨部',
    colProps: {
      span: 12
    },
    component: 'Select',
    componentProps: {
      style: {
        width: '100%'
      },
      multiple: false,
      props: {
        label: 'name_unique',
        value: 'id'
      }
    },
    optionApi: async () => {
      const res = await getKitchenListApi({is_active: true})
      return res.data
    },
    value: []
  },
  {
    field: 'price',
    label: '基础售价',
    colProps: {
      span: 12
    },
    component: 'Input',
    componentProps: {
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'order_number',
    label: '排序号',
    colProps: {
      span: 12
    },
    component: 'Input',
    componentProps: {
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'description',
    label: '简介',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      type: 'textarea',
      rows: 4,
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'description_english',
    label: '英文简介',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      type: 'textarea',
      rows: 4,
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'status',
    label: '状态',
    colProps: {
      span: 12
    },
    component: 'Select',
    componentProps: {
      style: {
        width: '100%'
      },
      options: props.dishStatusOptions,
      disabled: true
    },
    value: 0
  },
  {
    field: 'dish_images',
    label: '图片',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: (data) => {
          if (!data.dish_images) {
            data.dish_images = unref([])
            data.dish_images_display = unref([])
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

          const handleFileChange: UploadProps['onChange'] = (file, fileList) => {
            if (file.raw) {
              const exists = data.dish_images.some(item => item[2] === file.name)
              if (!exists) {
                const previewUrl = URL.createObjectURL(file.raw)
                data.dish_images_display.push(previewUrl)
                data.dish_images.push([previewUrl, 'add', file.name, file])
              }
            }
          }

          const handleremoveimage = (index) => {
            if (Array.isArray(data.dish_images[index])) {
              data.dish_images_display.splice(index, 1)
              data.dish_images.splice(index, 1)
            } else {
              data.dish_images_display[index] = `${data.dish_images_display[index].split('?')[0]}?delete`
              data.dish_images[index] = `${data.dish_images[index].split('?')[0]}?delete`
            }
          }

          const dragIndex = ref(-1)
          const dragOverIndex = ref(-1)

          const handleDragStart = (index, event) => {
            dragIndex.value = index
            event.dataTransfer.effectAllowed = 'move'
            event.dataTransfer.setData('text/plain', index.toString())

            setTimeout(() => {
              event.target.classList.add('dragging')
            }, 0)
          }

          const handleDragOver = (event) => {
            event.preventDefault()
            event.dataTransfer.dropEffect = 'move'
          }

          const handleDragEnter = (index, event) => {
            event.preventDefault()
            dragOverIndex.value = index
          }

          const handleDragLeave = (event) => {
            if (!event.currentTarget.contains(event.relatedTarget)) {
              dragOverIndex.value = -1
            }
          }

          const handleDrop = (targetIndex, event) => {
            event.preventDefault()
  
            const sourceIndex = parseInt(event.dataTransfer.getData('text/plain'))
            
            if (sourceIndex !== targetIndex && sourceIndex >= 0 && targetIndex >= 0) {
              const images_display = [...data.dish_images_display]
              if (images_display[1] === 'original') {
                images_display[1] = 'update'
              }
              const [movedItem1] = images_display.splice(sourceIndex, 1)
              images_display.splice(targetIndex, 0, movedItem1)
              data.dish_images_display = images_display

              const images_data = [...data.dish_images]
              if (images_data[1] === 'original') {
                images_data[1] = 'update'
              }
              const [movedItem2] = images_data.splice(sourceIndex, 1)
              images_data.splice(targetIndex, 0, movedItem2)
              data.dish_images = images_data
            }
            
            dragIndex.value = -1
            dragOverIndex.value = -1
          }

          const handleDragEnd = (event) => {
            dragIndex.value = -1
            dragOverIndex.value = -1
            
            const draggingElements = document.querySelectorAll('.dragging')
            draggingElements.forEach(el => {
              el.classList.remove('dragging')
            })
          }

          return (
            <div class="image-container">
              {data.dish_images_display?.map((image, index) => (
                image && !image.endsWith('?delete') && (
                  <div
                    key={`${index}-${image}`}
                    class={`image-group ${dragIndex.value === index ? 'dragging' : ''} ${dragOverIndex.value === index ? 'drag-over' : ''}`}
                    onClick={(e) => { e.stopPropagation(); }}
                    draggable="true"
                    onDragstart={(e) => handleDragStart(index, e)}
                    onDragover={handleDragOver}
                    onDragenter={(e) => handleDragEnter(index, e)}
                    onDragleave={handleDragLeave}
                    onDrop={(e) => handleDrop(index, e)}
                    onDragend={handleDragEnd}
                  >
                    <img src={image} class="image-item" />
                    <div onClick={(e) => { e.stopPropagation(); handleremoveimage(index);}} class="remove-btn">x</div>
                  </div>
                )
              ))}
              <div class="image-group-uploader">
                {(!data.dish_images_display || data.dish_images_display?.length < 10) && (
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
                    headers={{ Authorization: token }}
                    limit={10}
                  >
                    <div>
                      <ElIcon class="el-icon--upload"><UploadFilled /></ElIcon>
                      <div class="upload-text">拖拽文件到此或点击上传</div>
                    </div>
                  </ElUpload>
                )}
              </div>
            </div>
          )
        }
      }
    }
  }
])

const rules = reactive({
  name_unique: [required()],
  name_display: [required()],
  kitchen_id: [required()]
})

const { formRegister, formMethods } = useForm()
const { setValues, getFormData, getElFormExpose } = formMethods

const submit = async () => {
  const elForm = await getElFormExpose()
  const valid = await elForm?.validate()
  if (valid) {
    const formData = await getFormData()
    return formData
  }
}

watch(
  () => props.currentRow,
  (currentRow) => {
    if (!currentRow) return
    setValues(currentRow)
  },
  {
    deep: true,
    immediate: true
  }
)

defineExpose({
  submit
})
</script>

<template>
  <Form :rules="rules" :validate-on-rule-change="false" @register="formRegister" :schema="formSchema" />
</template>

<style lang="less">
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
    object-fit: cover;
    border: 1px solid #dcdfe6;
    transition: all 0.3s ease;
  }

  .image-item:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
</style>

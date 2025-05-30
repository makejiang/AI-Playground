<template>
    <div class="app-card">
        <!-- Add refresh icon button in the top right corner -->
        <div class="refresh-button" @click="refreshAppStatus" :class="{ 'refreshing': isRefreshing }">
            <div class="refresh-icon">↻</div>
        </div>
        
        <div class="app-info">
            <div class="app-icon">
                <img :src="`data:image/png;base64,${app.iconData}`" :alt="app.name" />
            </div>
            <div class="app-details">
                <h3 class="app-name">{{ app.nameCN }}</h3>
                <p class="app-tags">{{ app.tags.join(' | ') }}</p>

                <!-- <div class="app-rating">
                    <span class="rating-icon">⭐</span>
                    <span class="rating-score">{{ app.rating }}</span>
                </div> -->
                <!-- <div  v-if="status === 'installed'" style="display: flex; align-items: center; width: 100%; margin-top: 10px;">
                    <ProgressBar :percent="progress" :text="`${progress}%`" style="flex: 1;" />
                </div> -->
                <div style="align-items: center; width: 100%; margin-top: 10px;">
                    <label 
                        :id="labelId" 
                        :style="{
                            flex: 1,
                            color: statusColor(status), // Dynamically set color based on status
                            fontWeight: 'bold',
                            fontSize: '26px'
                        }"
                    >
                        {{ mapStatus(status) }}
                    </label>
                </div>
            </div>
            
        </div>        <div class="app-action">
            <button 
                class="install-btn" 
                @click="() => clickAction(status)" 
                :disabled="!app.installedname"
            >
                {{ btnText(status) }}
            </button>
            <button 
                v-show="status === 'installed'"
                class="install-btn uninstall-btn"                 
                @click="uninstallApp" 
                :disabled="!app.installedname"
            >
                卸载
            </button>
        </div>

        <!-- Moved progress bar to the bottom -->
        
    </div>
</template>
  
<script setup lang="ts">
import { useGlobalSetup } from '@/assets/js/store/globalSetup'
import { SSEProcessor } from '@/assets/js/sseProcessor'
import * as toast from '@/assets/js/toast'

const globalSetup = useGlobalSetup()

type AppStatus = 'not-installed' | 'installing' | 'installed' | 'running' | 'uninstalling' | 'not-supported'

interface App {
    name: string
    nameCN: string
    tags: string[]
    iconUrl: string
    iconData: string
    homeUrl: string
    installer: string
    processname: string
    installedname: string
    status: AppStatus
}

interface Props {
    app: App
    //status?: AppStatus
    progress?: number
    labelId?: string
}

// Export the App interface
export type { App, AppStatus }

const props = withDefaults(defineProps<Props>(), {
    status: 'not-installed',
    progress: 50,
    labelId: 'label'
})

// Reactive state
const status = ref<AppStatus>(props.app.status)
const isRefreshing = ref<boolean>(false)

// Watch for prop changes
watch(() => props.app.status, (newStatus) => {
    status.value = newStatus
})

// API request helper
const createRequestParams = () => ({
    app: {
        ...props.app,
        iconData: undefined // Remove iconData property from request
    }
})

function dataProcess(line: string) {
  const dataJson = line.slice(5) // Remove the "data: " prefix
  console.log('Processing SSE line:', dataJson)
  
  const data = JSON.parse(dataJson)
  console.log(data)

  status.value = data.state
}

const installApp = async (): Promise<void> => {
    console.log(`Installing ${props.app.name}...`)
    status.value = 'installing'

    fetch(`${globalSetup.apiHost}/api/app/installstream`, {
      method: 'POST',
      body: JSON.stringify(toRaw(createRequestParams())),
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then((response) => {
        const reader = response.body!.getReader()
        return new SSEProcessor(reader, dataProcess, undefined).start()
      })
      .catch((ex) => {
        status.value = 'not-installed'
      })
}

const uninstallApp = async (): Promise<void> => {
    console.log(`Uninstalling ${props.app.name}...`)
    status.value = 'uninstalling'

    fetch(`${globalSetup.apiHost}/api/app/uninstallstream`, {
      method: 'POST',
      body: JSON.stringify(toRaw(createRequestParams())),
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then((response) => {
        const reader = response.body!.getReader()
        return new SSEProcessor(reader, dataProcess, undefined).start()
      })
      .catch((ex) => {
        status.value = 'installed'
      })
}

const runApp = async (): Promise<void> => {
    console.log(`Running ${props.app.name}...`)

    try {
        const response = await fetch(`${globalSetup.apiHost}/api/app/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(createRequestParams()),
        })
        
        const data = await response.json()
        console.log('run result', data)

        if (data.result) {
            status.value = 'running'
        }
    } catch (error) {
        console.error('Error running app:', error)
    }
}

const closeApp = async (): Promise<void> => {
    console.log(`Closing ${props.app.name}...`)

    try {
        const response = await fetch(`${globalSetup.apiHost}/api/app/close`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(createRequestParams()),
        })
        
        const data = await response.json()
        console.log('close result', data)

        if (data.result) {
            status.value = 'installed'
        }
    } catch (error) {
        console.error('Error closing app:', error)
    }
}

const cancelInstallApp = (): void => {
    console.log(`Cancelling install of ${props.app.name}...`)
}

const cancelUninstallApp = (): void => {
    console.log(`Cancelling uninstall of ${props.app.name}...`)
}

const unknownAct = (): void => {
    console.log('You should not see this message')
}


const fetchAppStatus = async (): Promise<void> => {
    try {
        if (!props.app.installedname || !props.app.processname) {
            return
        }

        console.log(`app status: ${status.value}`)
        if (status.value === 'installing' || status.value === 'uninstalling') {
            console.log('Skip fetching status during installation or uninstallation')
            return
        }

        const response = await fetch(`${globalSetup.apiHost}/api/app/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(createRequestParams()),
        })

        const data = await response.json()
        console.log('Fetched app status:', data)

        if (data.status) {
            status.value = data.status
        }
    } catch (error) {
        console.error('Error fetching app status:', error)
    }
}

const refreshAppStatus = async (): Promise<void> => {
    if (isRefreshing.value) return
    
    isRefreshing.value = true
    console.log(`Refreshing status for ${props.app.name}...`)
    
    try {
        await fetchAppStatus()
    } catch (error) {
        console.error('Error refreshing app status:', error)
    } finally {
        // Add a small delay to make the animation visible
        setTimeout(() => {
            isRefreshing.value = false
        }, 500)
    }
}

// Computed functions for UI
const mapStatus = (currentStatus: AppStatus): string => {
    const statusMap: Record<AppStatus, string> = {
        'not-installed': '未安装',
        'installing': '安装中...',
        'installed': '已安装',
        'running': '运行中...',
        'uninstalling': '卸载中...',
        'not-supported': '不支持'
    }
    return statusMap[currentStatus] || '未知状态'
}

const btnText = (currentStatus: AppStatus): string => {
    const buttonTextMap: Record<AppStatus, string> = {
        'not-installed': '安装',
        'installing': '取消',
        'installed': '运行',
        'running': '关闭',
        'uninstalling': '取消',
        'not-supported': ''
    }
    return buttonTextMap[currentStatus] || '未知状态'
}

const clickAction = (currentStatus: AppStatus): Promise<void> | void => {
    const actionMap: Record<AppStatus, () => Promise<void> | void> = {
        'not-installed': installApp,
        'installing': cancelInstallApp,
        'installed': runApp,
        'running': closeApp,
        'uninstalling': cancelUninstallApp,
        'not-supported': () => {
            console.warn('This app is not supported')
        }
        
    }
    return actionMap[currentStatus]?.() || unknownAct()
}

const statusColor = (currentStatus: AppStatus): string => {
    const colorMap: Record<AppStatus, string> = {
        'not-installed': '#CE4912',
        'installing': '#F8D605',
        'installed': '#084387',
        'running': '#9cd261',
        'uninstalling': '#F8D605',
        'not-supported': '#CE4912'
    }
    return colorMap[currentStatus] || 'black'
}

// Lifecycle
onMounted(() => {
    console.log('CardApp mounted', props.app.name)
    if (!isRefreshing.value) {
        //fetchAppStatus()
    }
})



</script>
  
<style scoped>
  .app-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    border-radius: 10px;
    background-color: #ffffff86;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative; /* Add position relative for absolute positioning of refresh button */
  }
  
  .app-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
  }
  
  .app-info {
    display: flex;
    align-items: center;
  }
  
  .app-icon {
    width: 128px;
    height: 128px;
    margin-right: 15px;
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center; /* Center the img vertically */
  }
  
  .app-icon img {
    width: 100%;
    object-fit: cover;
  }
  
  .app-details {
    flex: 1;
  }
  
  .app-name {
    margin: 0 0 5px;
    font-size: 22px;
    font-weight: bold;
  }
  
  .app-tags {
    margin: 0 0 5px;
    font-size: 14px;
    
    color: #353535;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 200px;
  }
  
  .app-rating {
    display: flex;
    align-items: center;
  }
  
  .rating-icon {
    color: #ffb800;
    margin-right: 5px;
  }
  
  .rating-score {
    font-size: 16px;
    color: #353535;
  }
  
  .app-action {
    margin-left: 0px;
    display: flex;
    flex-direction: column; /* Arrange buttons vertically */
    row-gap: 5px; /* Add 10px gap between buttons */
  }
  
  .install-btn {
    padding: 8px 20px;
    width: 100px;
    border-radius: 20px;
    border: none;
    font-size: 20px;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.2s;
    background-color: #0088ff;
    color: white;
  }
  
  .install-btn:hover {
    background-color: #0054a3;
  }

  .uninstall-btn {
    padding: 8px 20px;
    width: 100px;
    border-radius: 20px;
    border: none;
    font-size: 20px;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.2s;
    background-color: #ff4d4f; /* Red background for uninstall button */
    color: white;
  }

  .uninstall-btn:hover {
    background-color: #d9363e; /* Darker red on hover */
  }

  /* Styles for the refresh button */
  .refresh-button {
    position: absolute;
    top: 10px;
    left: 10px;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background-color: rgba(255, 255, 255, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    z-index: 2;
    transition: background-color 0.2s;
  }
  
  .refresh-button:hover {
    background-color: rgba(0, 136, 255, 0.2);
  }
  
  .refresh-icon {
    font-size: 20px;
    color: #0088ff;
    transition: transform 0.5s ease;
  }
  
  /* Add spinning animation when refreshing */
  .refreshing .refresh-icon {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
</style>
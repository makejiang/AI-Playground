<template>
    <div class="app-card">
        <!-- Add refresh icon button in the top right corner -->
        <div class="refresh-button" @click="refreshAppStatus" :class="{ 'refreshing': isRefreshing }">
            <div class="refresh-icon">↻</div>
        </div>
        
        <div class="app-info">
            <div class="app-icon">
                <img :src="app.iconUrl" :alt="app.name" />
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
            
        </div>
        <div class="app-action">
            <button 
                class="install-btn" 
                @click="clickAction(status)" 
                :disabled="!app.installedname">
                {{ btnText(status) }}
            </button>
            <button 
                v-if="status === 'installed'"
                class="install-btn uninstall-btn"                 
                @click="uninstallApp()" 
                :disabled="!app.installedname">
                卸载
            </button>
        </div>

        <!-- Moved progress bar to the bottom -->
        
    </div>
</template>
  
<script setup lang="ts">
import { emitter } from '@/assets/js/util'
import { useGlobalSetup } from '@/assets/js/store/globalSetup'
import ProgressBar from './ProgressBar.vue';
import { Prop } from 'vue';

const globalSetup = useGlobalSetup()

interface App {
    name: string;
    nameCN: string;
    tags: string[];
    iconUrl: string;
    homeUrl: string;
    installer: string;
    processname: string;
    installedname: string;
}

const props = defineProps({
    app: {
        type: Object as PropType<App>,
        required: true,
    },
    status: {
        type: String,
        default: 'not-installed',
    },
    progress: {
        type: Number,
        default: 50, // Progress percentage
    },
    labelId: {
        type: String,
        default: 'label',
    },
});


const status = ref(props.status); // Make status reactive
watch(() => props.status, (newStatus) => {
    status.value = newStatus; // Sync props.status with local reactive status
});

const emit = defineEmits(['update-status']); // Define an event to notify parent

onMounted(() => {
  //console.log('CardApp mounted');
})

let fetchStatusTimeout: number | null = null; // Store the timeout ID

async function installApp() {
    console.log(`Installing ${props.app.name}...`);

    //clearFetchStatusTimeout(); // Stop the fetchAppStatus timeout
    status.value = 'installing'; // Update local reactive status
    emit('update-status', 'installing'); // Notify parent about the status change

    try {
        const requestParams = {
            app: props.app,
        };

        const response = await fetch(`${globalSetup.apiHost}/api/app/install`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestParams),
        });
        const data = await response.json();
        console.log('install result', data);

        if (data.result) {
            status.value = 'installed'; // Update status to installed
            emit('update-status', 'installed'); // Notify parent about the status change
        } else {
            status.value = 'not-installed'; // Revert status on failure
            emit('update-status', 'not-installed'); // Notify parent about the status change
        }
    } catch (error) {
        console.error('Error fetching app status:', error);
    }
}

async function uninstallApp() {
    console.log(`Uninstalling ${props.app.name}...`);

    //clearFetchStatusTimeout(); // Stop the fetchAppStatus timeout
    status.value = 'uninstalling'; // Update local reactive status
    emit('update-status', 'uninstalling'); // Notify parent about the status change

    try {
        const requestParams = {
            app: props.app,
        };

        const response = await fetch(`${globalSetup.apiHost}/api/app/uninstall`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestParams),
        });
        const data = await response.json();
        console.log('uninstall result', data);

        if (data.result) {
            status.value = 'not-installed'; // Update status to non-installed
            emit('update-status', 'not-installed'); // Notify parent about the status change
        } else {
            status.value = 'installed'; // Revert status on failure
            emit('update-status', 'installed'); // Notify parent about the status change
        }
    } catch (error) {
        console.error('Error fetching app status:', error);
    }
}

async function runApp() {
    console.log(`Run ${props.app.name}...`);

    //status.value = 'uninstalling';    
    //emit('update-status', 'uninstalling'); // Notify parent about the status change

    try {
        const requestParams = {
            app: props.app,
        };

        const response = await fetch(`${globalSetup.apiHost}/api/app/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestParams),
        });
        const data = await response.json();
        console.log('run result', data);

        if (data.result) {
            status.value = 'running'; // Update status to non-installed
            emit('update-status', 'running'); // Notify parent about the status change
        }

    } catch (error) {
        console.error('Error fetching app status:', error);
    }
}

async function closeApp() {
    console.log(`Close ${props.app.name}...`);

    try {
        const requestParams = {
            app: props.app,
        };

        const response = await fetch(`${globalSetup.apiHost}/api/app/close`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestParams),
        });
        const data = await response.json();
        console.log('run result', data);

        if (data.result) {
            status.value = 'installed'; // Update status to non-installed
            emit('update-status', 'installed'); // Notify parent about the status change
        }

    } catch (error) {
        console.error('Error fetching app status:', error);
    }
}

async function cancelInstallApp() {
    console.log(`Cancel Install ${props.app.name}...`);
}

async function cancelUninstallApp() {
    console.log(`Cancel Uninstall ${props.app.name}...`);
}

async function unknownAct() {
    console.log('you should not see this message');
}


async function fetchAppStatus() {
    try {
        if (!props.app.installedname || !props.app.processname) {   // Check if app name is provided
            //console.error(`App(${props.app.name}) info not provided`);
            return;
        }
        console.log(`app status: ${status.value} `);
        if (status.value === 'installing' || status.value === 'uninstalling') {
            console.log('Skip fetching status during installation or uninstallation');
            return;
        }

        const requestParams = {
            app: props.app,
        };
        const response = await fetch(`${globalSetup.apiHost}/api/app/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestParams),
        });
        const data = await response.json();
        console.log('Fetched app status:', data);

        if (data.status) {
            status.value = data.status; // Update local reactive status
            emit('update-status', data.status); // Notify parent about the status change
        }

    } catch (error) {
        console.error('Error fetching app status:', error);
    }

    //fetchStatusTimeout = window.setTimeout(fetchAppStatus, 2000); // Schedule the next fetch
}

emitter.on('backendReady', () => {
    fetchAppStatus(); // Start fetching app status
});
// Fetch app status during initialization
//fetchStatusTimeout = window.setTimeout(fetchAppStatus, 1500);

function clearFetchStatusTimeout() {
    if (fetchStatusTimeout !== null) {
        clearTimeout(fetchStatusTimeout); // Clear the timeout
        fetchStatusTimeout = null;
    }
}

const mapStatus = (currentStatus: string): string => {
    switch (currentStatus) {
        case 'not-installed':
            return '未安装';
        case 'installing':
            return '安装中...';
        case 'installed':
            return '已安装';
        case 'running':
            return '运行中...';
        case 'uninstalling':
            return '卸载中...';
        default:
            return '未知状态';
    }
};

const btnText = (currentStatus: string): string => {
    switch (currentStatus) {
        case 'not-installed':
            return '安装';
        case 'installing':
            return '取消';
        case 'installed': // but not running
            return '运行';
        case 'running':
            return '关闭';
        case 'uninstalling':
            return '取消';
        default:
            return '未知状态';
    }
};

const clickAction = (currentStatus: string) => {
    switch (currentStatus) {
        case 'not-installed':
            return installApp();
        case 'installing':
            return cancelInstallApp(); // Warning color for installing
        case 'installed':
            return runApp(); // Success color for installed
        case 'running':
            return closeApp(); // Active color for running
        case 'uninstalling':
            return cancelUninstallApp(); // Danger color for uninstalling
        default:
            return unknownAct(); // Default color for unknown status
    }
};

const statusColor = (currentStatus: string): string => {
    switch (currentStatus) {
        case 'not-installed':
            return '#CE4912'; // Neutral color for not installed
        case 'installing':
            return '#F8D605'; // Warning color for installing
        case 'installed':
            return '#084387'; // Success color for installed
        case 'running':
            return '#9cd261'; // Active color for running
        case 'uninstalling':
            return '#F8D605'; // Danger color for uninstalling
        default:
            return 'black'; // Default color for unknown status
    }
};

// Add state variable for tracking refresh status
const isRefreshing = ref(false);

// Function to handle refresh button click
async function refreshAppStatus() {
    if (isRefreshing.value) return; // Prevent multiple refreshes
    
    isRefreshing.value = true;
    console.log(`Refreshing status for ${props.app.name}...`);
    
    try {
        await fetchAppStatus();
    } catch (error) {
        console.error('Error refreshing app status:', error);
    } finally {
        // Add a small delay before setting isRefreshing to false
        // to make the animation visible even for quick refreshes
        setTimeout(() => {
            isRefreshing.value = false;
        }, 500);
    }
}

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
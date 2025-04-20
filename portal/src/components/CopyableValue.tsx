import {CopyToClipboard, SpaceBetween} from "@cloudscape-design/components";

const CopyableValue: React.FC<{ label: string; value: string, display?: string | null }> = ({
                                                                                                label,
                                                                                                value,
                                                                                                display = null
                                                                                            }) => (
    <div>
        <SpaceBetween size={"m"} direction={"horizontal"} alignItems={"center"}>
            {display ? display : value}
            {
                value.length > 1 && <CopyToClipboard
                    copyButtonText="copy"
                    copyErrorText={`Failed to copy ${label}`}
                    copySuccessText={`${label} copied to clipboard`}
                    textToCopy={value}
                />
            }</SpaceBetween></div>

);

export default CopyableValue;
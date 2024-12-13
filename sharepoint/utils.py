import re


def replace_string_map(word: str, replace_map: dict, reverse=False):
    if reverse:
        replace_map = {val: key for key, val in replace_map.items()}
    for target, replace in replace_map.items():
        word = word.replace(target, replace)
    return word


def replace_key_mapping(dictionary: dict, replace_map: dict, reverse=False):
    if reverse:
        replace_map = {val: key for key, val in replace_map.items()}
    result = {}
    for key, value in dictionary.items():
        key = replace_string_map(key, replace_map)
        result[key] = value
    return result


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


def to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


COLUMN_ESCAPE = {'~': '_x007e_', '!': '_x0021_', '@': '_x0040_',
                 '#': '_x0023_', '$': '_x0024_', '%': '_x0025_',
                 '^': '_x005e_', '&': '_x0026_', '*': '_x002a_',
                 '(': '_x0028_', ')': '_x0029_', '+': '_x002b_',
                 '–': '_x002d_', '=': '_x003d_', '{': '_x007b_',
                 '}': '_x007d_', ':': '_x003a_', '“': '_x0022_',
                 '|': '_x007c_', ';': '_x003b_', '‘': '_x0027_',
                 '\\': '_x005c_', '<': '_x003c_', '>': '_x003e_',
                 '?': '_x003f_', ',': '_x002c_', '.': '_x002e_',
                 '/': '_x002f_', '`': '_x0060_', " ": '_x0020_'}
AUTO_LIST_FIELDS = {'AccessPolicy', 'AppAuthor', 'AppEditor', 'Attachments', 'BaseName', 'ComplianceAssetId',
                    'ContentType', 'ContentTypeId', 'ContentVersion', 'Created_x0020_Date', 'DocIcon', 'Edit', 'Editor',
                    'EncodedAbsUrl', 'FSObjType', 'FileDirRef', 'FileLeafRef', 'FileRef', 'File_x0020_Type',
                    'FolderChildCount', 'HTML_x0020_File_x0020_Type', 'ID', 'InstanceID', 'ItemChildCount',
                    'Last_x0020_Modified', 'LinkFilename', 'LinkFilename2', 'LinkFilenameNoMenu', 'LinkTitle',
                    'LinkTitle2', 'LinkTitleNoMenu', 'MetaInfo', 'NoExecute', 'Order', 'OriginatorId', 'ParentUniqueId',
                    'PermMask', 'PrincipalCount', 'ProgId', 'Restricted', 'SMLastModifiedDate', 'SMTotalFileCount',
                    'SMTotalFileStreamSize', 'SMTotalSize', 'ScopeId', 'SelectTitle', 'ServerUrl', 'SortBehavior',
                    'SyncClientId', 'Title', 'UniqueId', 'WorkflowInstanceID', 'WorkflowVersion', '_CommentCount',
                    '_CommentFlags', '_ComplianceFlags', '_ComplianceTag', '_ComplianceTagUserId',
                    '_ComplianceTagWrittenTime', '_CopySource', '_EditMenuTableEnd', '_EditMenuTableStart',
                    '_EditMenuTableStart2', '_HasCopyDestinations', '_IsCurrentVersion', '_IsRecord', '_Level',
                    '_ModerationComments', '_ModerationStatus', '_UIVersion', '_UIVersionString', '_VirusInfo',
                    '_VirusStatus', '_VirusVendorID',
                    'Modified_x0020_By', 'owshiddenversion', '_DisplayName', '_IpLabelPromotionCtagVersion',
                    'CheckedOutTitle', 'xd_Signature', 'BSN', '_IpLabelHash', 'TriggerFlowInfo', '_HasEncryptedContent',
                    'Author', 'FileSizeDisplay', '_SharedFileIndex', 'DocConcurrencyNumber', '_CheckinComment',
                    'Created_x0020_By', '_ExtendedDescription', 'StreamHash', 'VirusStatus', '_RmsTemplateId',
                    '_IpLabelAssignmentMethod', 'A2ODMountCount', 'xd_ProgID', '_Dirty', '_ShortcutWebId', '_LikeCount',
                    '_StubFile', 'Modified', 'ParentVersionString', 'File_x0020_Size', 'LinkCheckedOutTitle',
                    'ParentLeafName', '_ShortcutUniqueId', 'GUID', '_IpLabelId', 'Combine', 'CheckoutUser',
                    'TemplateUrl', 'RepairDocument', '_ShortcutUrl', 'CheckedOutUserId', 'SelectFilename',
                    '_ShortcutSiteId', 'PolicyDisabledUICapabilities', '_ExpirationDate', '_ListSchemaVersion',
                    'IsCheckedoutToLocal', '_SourceUrl', '_HasUserDefinedProtection', 'Created', '_Parsable'}
AUTO_ITEM_PROPERTIES = {"AttachmentFiles", "AuthorId", "CheckoutUserId", "ComplianceAssetId",
                        "ContentType", "ContentTypeId", "Created", "Deferred", "Sharepoint", "Uri", "EditorId",
                        "FieldValuesAsHtml", "FieldValuesAsText", "Type",
                        "FieldValuesForEdit", "File", "FileSystemObjectType", "FirstUniqueAncestorSecurableObject",
                        "Folder", "GUID", "GetDlpPolicyTip", "ID", "Id", "LikedByInformation", "Modified",
                        "OData__CopySource", "OData__UIVersionString", "ParentList", "Properties", "RoleAssignments",
                        "ServerRedirectedEmbedUri", "ServerRedirectedEmbedUrl", "Title", "Versions", "__metadata",
                        "Attachments"}
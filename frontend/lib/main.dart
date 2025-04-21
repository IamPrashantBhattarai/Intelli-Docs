import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart';
import 'package:open_filex/open_filex.dart';
import 'screens/gallery_screen.dart';
import 'package:http/http.dart' as http;
import 'package:mime/mime.dart';
import 'package:http_parser/http_parser.dart';

void main() {
  runApp(ChatApp());
}

class ChatApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'IntelliDocs',
      theme: ThemeData(
        primaryColor: Color(0xFF10A37F),
        scaffoldBackgroundColor: Colors.white,
        fontFamily: 'Inter',
      ),
      home: ChatScreen(), // Add this line
    );
  }
}

class ChatScreen extends StatefulWidget {
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final List<Map<String, dynamic>> _messages = [];
  final FocusNode _focusNode = FocusNode();

  int key = 0; //🔑 State variable for tracking mode

  void _setMode(int newKey) {
    setState(() {
      key = newKey; // Updates the mode based on button pressed
    });
    print("🔄 Mode changed! Current key: $key");
  }

  Future<void> uploadFile(File file) async {
    print('🚀 Upload function called with file: ${file.path}');

    final String url = "http://172.20.10.8:3000/api/upload";

    try {
      var request = http.MultipartRequest('POST', Uri.parse(url));
      print('🛠 Creating Multipart request...');

      String? mimeType = lookupMimeType(file.path);
      var multipartFile = await http.MultipartFile.fromPath(
        'file',
        file.path,
        contentType: mimeType != null ? MediaType.parse(mimeType) : null,
      );

      request.files.add(multipartFile);
      request.fields['user_id'] = '123';

      print('📡 Sending request...');
      var response = await request.send();

      print('✅ Server responded with status: ${response.statusCode}');
      if (response.statusCode == 200) {
        print('✅ File uploaded successfully');
      } else {
        print('❌ Failed to upload file: ${response.statusCode}');
      }
    } catch (e) {
      print('⚠️ Error uploading file: $e');
    }
  }

  Future<void> _addImage() async {
    final picker = ImagePicker();
    final XFile? pickedFile =
        await picker.pickImage(source: ImageSource.gallery);
    if (pickedFile != null) _handleFile(File(pickedFile.path), isImage: true);
  }

  Future<void> _takePhoto() async {
    final picker = ImagePicker();
    final XFile? pickedFile =
        await picker.pickImage(source: ImageSource.camera);

    if (pickedFile != null) {
      print("📸 Captured Image Path: ${pickedFile.path}");

      File imageFile = File(pickedFile.path);
      setState(() {
        _messages.add({
          'type': 'image',
          'filePath': pickedFile.path, // Correct file path
          'sender': 'user'
        });
      });

      await uploadFile(imageFile);
      _addBotResponse("Thanks for the image!");
    } else {
      print("⚠️ No image captured.");
    }
  }

  Future<void> _addFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles();
    if (result != null && result.files.single.path != null) {
      _handleFile(File(result.files.single.path!));
    }
  }

  Future<void> _handleFile(File file, {bool isImage = false}) async {
    final filePath = file.path;
    print("📂 File Added: $filePath");

    setState(() {
      _messages.add({
        'type': isImage ? 'image' : 'file',
        'filePath': filePath,
        'sender': 'user'
      });
    });

    await uploadFile(file);
    _addBotResponse("Thanks for the ${isImage ? 'image' : 'file'}!");
  }

  Future<void> _fetchBotResponse(String userMessage) async {
    final String url = "http://172.20.10.8:3000/api/process-input/$key";

    setState(() {
      _messages.add({
        'type': 'text',
        'content': "🤔 Thinking...",
        'sender': 'bot',
        'isLoading': true, // A flag to identify loading messages
      });
    });

    try {
      print("📡 Sending request to $url with key: $key...");
      var request = http.MultipartRequest('POST', Uri.parse(url));
      request.fields['text_prompt'] = userMessage;

      var response = await request.send();
      String botResponse = await response.stream.bytesToString();

      setState(() {
        _messages.removeWhere(
            (msg) => msg['isLoading'] == true); // Remove "thinking..."
        _addBotResponse(botResponse);
      });
    } catch (e) {
      print("⚠️ Exception: $e");
      setState(() {
        _messages.removeWhere((msg) => msg['isLoading'] == true);
        _addBotResponse("Error: Connection failed.");
      });
    }
  }

  void _sendMessage() async {
    if (_controller.text.isEmpty) return;

    String userMessage = _controller.text;

    setState(() {
      _messages.add({'type': 'text', 'content': userMessage, 'sender': 'user'});
      _controller.clear();
    });

    await _fetchBotResponse(userMessage); // Now passing key
  }

  void _addBotResponse(String content) {
    Future.delayed(Duration(seconds: 1), () {
      setState(() {
        try {
          // Check if response is JSON
          Map<String, dynamic> botResponse = jsonDecode(content);

          if (botResponse.containsKey('response')) {
            var responseData = botResponse['response'];

            if (responseData is List) {
              // If it's a list, assume it's image URLs
              for (var url in responseData) {
                _messages.add({
                  'type': 'image',
                  'filePath': url.toString(),
                  'sender': 'bot'
                });
              }
            } else if (responseData is String) {
              // If it's a string, assume it's text
              _messages.add(
                  {'type': 'text', 'content': responseData, 'sender': 'bot'});
            } else {
              _messages.add({
                'type': 'text',
                'content': "Unexpected response format",
                'sender': 'bot'
              });
            }
          } else {
            _messages.add({
              'type': 'text',
              'content': "Invalid response",
              'sender': 'bot'
            });
          }
        } catch (e) {
          print("⚠️ Error processing response: $e");
          _messages
              .add({'type': 'text', 'content': "File Saved", 'sender': 'bot'});
        }
      });
    });
  }

  void _openFile(String filePath) => OpenFilex.open(filePath);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title:
            Text('IntelliDocs', style: TextStyle(fontWeight: FontWeight.w600)),
        centerTitle: false,
        elevation: 2,
        shadowColor: Colors.black12,
        actions: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: ClipOval(
              child: Material(
                color: Colors.transparent, // Transparent background
                child: InkWell(
                  splashColor: Colors.grey.withOpacity(0.2), // Button effect
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => GalleryScreen(files: _messages),
                      ),
                    );
                    print("Image button pressed");
                  },
                  child: Ink.image(
                    image: AssetImage('assets/logo/app_logo.jpg'),
                    width: 40,
                    height: 40,
                    fit: BoxFit.cover,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                final isUser = message['sender'] == 'user';

                return Container(
                  margin: EdgeInsets.only(bottom: 12),
                  child: Row(
                    mainAxisAlignment: isUser
                        ? MainAxisAlignment.end
                        : MainAxisAlignment.start,
                    children: [
                      if (!isUser) ...[
                        Padding(
                          padding: const EdgeInsets.only(right: 8.0),
                          child: CircleAvatar(
                            backgroundColor: Colors.transparent,
                            backgroundImage:
                                AssetImage('assets/logo/app_logo.jpg'),
                            radius: 20, // Adjust size as needed
                          ),
                        ),
                        SizedBox(width: 8),
                      ],
                      ConstrainedBox(
                        constraints: BoxConstraints(
                            maxWidth: MediaQuery.of(context).size.width * 0.75),
                        child: Container(
                          padding: EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color:
                                isUser ? Color(0xFF10A37F) : Color(0xFFF7F7F8),
                            borderRadius: BorderRadius.only(
                              topLeft: Radius.circular(12),
                              topRight: Radius.circular(12),
                              bottomLeft: isUser
                                  ? Radius.circular(12)
                                  : Radius.circular(4),
                              bottomRight: isUser
                                  ? Radius.circular(4)
                                  : Radius.circular(12),
                            ),
                          ),
                          child: _buildMessageContent(message, isUser: isUser),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
          _buildActionButtons(),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildMessageContent(Map<String, dynamic> message,
      {required bool isUser}) {
    if (message['type'] == 'text') {
      return Text(
        message['content'],
        style: TextStyle(
            color: isUser ? Colors.white : Colors.black, fontSize: 16),
      );
    }

    if (message['type'] == 'image') {
      final filePath = message['filePath'];
      final isNetworkImage = filePath.startsWith('http');
      return ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: isNetworkImage
            ? Image.network(
                filePath,
                height: 200,
                width: 200,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) {
                  return Text("Error loading image");
                },
              )
            : Image.file(
                File(filePath),
                height: 200,
                width: 200,
                fit: BoxFit.cover,
              ),
      );
    }

    return InkWell(
      onTap: () => _openFile(message['filePath']),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.insert_drive_file,
              color: isUser ? Colors.white70 : Colors.grey),
          SizedBox(width: 8),
          Text(basename(message['filePath'])),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildActionButton(Icons.home, "Automode", 0, Colors.blueAccent),
          _buildActionButton(
              Icons.description, "Text_Extract", 1, Colors.redAccent),
          _buildActionButton(
              Icons.photo_library, "Image_Retriev", 2, Colors.greenAccent),
          _buildActionButton(
              Icons.personal_injury_rounded, "Freewill", 3, Colors.grey),
        ],
      ),
    );
  }

  /// Builds a single action button with shadow effect when selected
  Widget _buildActionButton(
      IconData icon, String label, int mode, Color activeColor) {
    bool isActive = key == mode; // Check if this button is active

    return Column(
      children: [
        Container(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            boxShadow: isActive
                ? [
                    BoxShadow(
                      color: activeColor.withOpacity(0.5), // Glowing effect
                      spreadRadius: 4,
                      blurRadius: 8,
                      offset: Offset(
                          0, 2), // Adjusted for a slight elevation effect
                    )
                  ]
                : [], // No shadow when inactive
          ),
          child: IconButton(
            icon: Icon(icon, color: isActive ? activeColor : Colors.grey),
            onPressed: () {
              _setMode(mode);
            },
          ),
        ),
        Text(label,
            style: TextStyle(
                fontSize: 12, color: isActive ? activeColor : Colors.grey)),
      ],
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: Colors.grey.shade200)),
      ),
      child: Row(
        children: [
          PopupMenuButton<String>(
            icon: Icon(Icons.add, color: Color(0xFF10A37F)),
            itemBuilder: (context) => [
              PopupMenuItem(value: 'photo', child: Text('Photo Library')),
              PopupMenuItem(value: 'camera', child: Text('Take Photo')),
              PopupMenuItem(value: 'file', child: Text('Upload File')),
            ],
            onSelected: (value) {
              if (value == 'photo') _addImage();
              if (value == 'camera') _takePhoto();
              if (value == 'file') _addFile();
            },
          ),
          Expanded(
            child: TextField(
              controller: _controller,
              focusNode: _focusNode,
              decoration: InputDecoration(
                hintText: 'Message...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                filled: true,
                fillColor: Colors.grey.shade100,
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          SizedBox(width: 8),
          Container(
            decoration: BoxDecoration(
              color: Color(0xFF10A37F),
              shape: BoxShape.circle,
            ),
            child: IconButton(
              icon: Icon(Icons.send, color: Colors.white),
              onPressed: _sendMessage,
            ),
          ),
        ],
      ),
    );
  }
}

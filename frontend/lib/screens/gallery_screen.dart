import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path/path.dart' as p;
import 'package:http/http.dart' as http;

class GalleryScreen extends StatefulWidget {
  final List<Map<String, dynamic>> files;

  GalleryScreen({required this.files});

  @override
  _GalleryScreenState createState() => _GalleryScreenState();
}

class _GalleryScreenState extends State<GalleryScreen> {
  List<String> cloudinaryImages = [];
  List<String> cloudinaryFiles = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchCloudinaryData();
  }

  Future<void> fetchCloudinaryData() async {
    final String apiUrl =
        "http://172.20.10.8:3000/api/files"; // Your backend URL

    try {
      final response = await http.get(Uri.parse(apiUrl));

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);

        if (data.containsKey('files') && data['files'] is List) {
          List<dynamic> filesList = data['files'];

          setState(() {
            cloudinaryImages = filesList
                .where((file) =>
                    file['format'] == 'jpg' ||
                    file['format'] == 'png' ||
                    file['format'] == 'jpeg') // Filter image formats
                .map((file) => file['url'] as String)
                .toList();

            cloudinaryFiles = filesList
                .where((file) =>
                    file['format'] == 'pdf' ||
                    file['format'] == 'application/pdf') // Filter PDFs
                .map((file) => file['url'] as String)
                .toList();

            isLoading = false;
          });
        } else {
          throw Exception("Invalid response format: Expected a 'files' list.");
        }
      } else {
        throw Exception("Failed to load Cloudinary data.");
      }
    } catch (e) {
      print("Error fetching images and files: $e");
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final List<Map<String, dynamic>> images = widget.files
        .where((file) => file['type'] == 'image' && file['filePath'] != null)
        .toList();
    final List<Map<String, dynamic>> documents = widget.files
        .where((file) => file['type'] == 'file' && file['filePath'] != null)
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Gallery & Files'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: ListView(
          children: [
            _buildSection(
              title: "Cloudinary Gallery",
              items: cloudinaryImages,
              isImage: true,
              isCloudinary: true,
            ),
            _buildSection(
              title: "Cloudinary PDFs",
              items: cloudinaryFiles,
              isImage: false,
              isCloudinary: true,
            ),
            _buildSection(
              title: "Local Gallery",
              items: images,
              isImage: true,
              isCloudinary: false,
            ),
            _buildSection(
              title: "Files",
              items: documents,
              isImage: false,
              isCloudinary: false,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection({
    required String title,
    required List<dynamic> items,
    required bool isImage,
    required bool isCloudinary,
  }) {
    return ExpansionTile(
      initiallyExpanded: true,
      title: Text(
        title,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
      ),
      children: items.isNotEmpty
          ? [
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 3,
                  crossAxisSpacing: 8,
                  mainAxisSpacing: 8,
                ),
                itemCount: items.length,
                itemBuilder: (context, index) {
                  return isCloudinary
                      ? (isImage
                          ? _buildCloudinaryImage(items[index])
                          : _buildCloudinaryFile(items[index])) // Fix for PDFs
                      : _buildFileItem(items[index], isImage: isImage);
                },
              ),
            ]
          : [
              Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  "No ${isImage ? 'images' : 'files'} available.",
                  style: const TextStyle(color: Colors.grey),
                ),
              )
            ],
    );
  }

  Widget _buildCloudinaryImage(String imageUrl) {
    return GestureDetector(
      onTap: () {
        // Optionally allow users to open image in full screen
        showDialog(
          context: context,
          builder: (context) => Dialog(
            child: Image.network(imageUrl),
          ),
        );
      },
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Image.network(
          imageUrl,
          fit: BoxFit.cover,
          loadingBuilder: (context, child, loadingProgress) {
            if (loadingProgress == null) return child;
            return const Center(child: CircularProgressIndicator());
          },
          errorBuilder: (context, error, stackTrace) =>
              _imageErrorPlaceholder(),
        ),
      ),
    );
  }

  Widget _buildFileItem(Map<String, dynamic> file, {required bool isImage}) {
    final String? filePath = file['filePath'];

    return GestureDetector(
      onTap: () {
        if (filePath != null && filePath.isNotEmpty) {
          try {
            OpenFilex.open(filePath);
          } catch (e) {
            debugPrint("Error opening file: $e");
          }
        }
      },
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          color: Colors.grey.shade200,
        ),
        child: filePath != null && filePath.isNotEmpty
            ? isImage
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.file(
                      File(filePath),
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) =>
                          _imageErrorPlaceholder(),
                    ),
                  )
                : Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.insert_drive_file,
                          size: 40, color: Colors.grey),
                      const SizedBox(height: 4),
                      Text(
                        p.basename(filePath),
                        textAlign: TextAlign.center,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 12),
                      ),
                    ],
                  )
            : _fileErrorPlaceholder(isImage),
      ),
    );
  }

  Widget _buildCloudinaryFile(String fileUrl) {
    return GestureDetector(
      onTap: () async {
        try {
          await OpenFilex.open(fileUrl);
        } catch (e) {
          print("Error opening file: $e");
        }
      },
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          color: Colors.grey.shade200,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.picture_as_pdf, size: 40, color: Colors.redAccent),
            const SizedBox(height: 4),
            Text(
              fileUrl.split('/').last, // Extract filename from URL
              textAlign: TextAlign.center,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _imageErrorPlaceholder() {
    return Container(
      alignment: Alignment.center,
      color: Colors.grey.shade300,
      child: const Icon(Icons.broken_image, size: 40, color: Colors.grey),
    );
  }

  Widget _fileErrorPlaceholder(bool isImage) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          isImage ? Icons.broken_image : Icons.error_outline,
          size: 40,
          color: Colors.redAccent,
        ),
        const SizedBox(height: 4),
        const Text(
          "File not found",
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 12, color: Colors.redAccent),
        ),
      ],
    );
  }
}
